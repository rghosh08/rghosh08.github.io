#!/usr/bin/env python3
"""Von Semantic Router: a tiny local web app that routes coding requests to Claude.

Run:   python3 router.py          then open http://127.0.0.1:8766
Needs: Python 3.8+, no third-party packages, and a running Von server
       (pip install von-sdk, then von serve; it listens on port 8000).

The page (public/jev-router.html) asks Von, an open-source System One decision
model (https://huggingface.co/wfzyx/von), how hard a coding request is, picks
the cheapest Claude tier (Haiku, Sonnet, Opus) whose cumulative probability
reaches the coverage threshold, and streams that model's answer. This server
serves the page and forwards both calls. The Von call goes to VON_BASE_URL
(default http://127.0.0.1:8000, or the address typed into the page) with
VON_API_KEY as the bearer token if the Von server requires one. Keys are sent
with each request and never written to disk. Empty key fields fall back to
the VON_API_KEY and ANTHROPIC_API_KEY environment variables.

The same page is published at https://rajatghosh.me/jev-router.html, where
the browser calls the Von server directly (Von allows cross-origin calls by
default) and the Claude call goes straight to api.anthropic.com.
"""
import argparse
import atexit
import json
import os
import shutil
import signal
import subprocess
import tempfile
import threading
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ANTHROPIC_URL = os.environ.get("ANTHROPIC_API_URL", "https://api.anthropic.com/v1/messages")
VON_BASE_URL = os.environ.get("VON_BASE_URL", "http://127.0.0.1:8000")
INDEX = Path(__file__).resolve().parent.parent / "public" / "jev-router.html"
MAX_BODY = 2 * 1024 * 1024
ALLOWED_MODELS = {"claude-haiku-5-5", "claude-sonnet-5-5", "claude-opus-5-5"}


def find_von():
    """The `von` executable the Start button runs: VON_BIN, ~/.venvs/von, or PATH."""
    for cand in (os.environ.get("VON_BIN"), Path.home() / ".venvs" / "von" / "bin" / "von", shutil.which("von")):
        if cand and Path(cand).is_file() and os.access(cand, os.X_OK):
            return str(cand)
    return None


VON_BIN = find_von()
_von_lock = threading.Lock()
_von_proc = None      # the `von serve` child started from the page, if any
_von_log = None       # its log file path


def von_health(base_url):
    """GET /health on a Von server. Returns its JSON body, or None when it is not up."""
    try:
        with urllib.request.urlopen(base_url.rstrip("/") + "/health", timeout=2) as resp:
            body = json.loads(resp.read())
            return body if isinstance(body, dict) else {}
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return None


def von_state():
    """What the page shows in its Von status line."""
    health = von_health(VON_BASE_URL)
    host = urllib.parse.urlsplit(VON_BASE_URL).hostname or ""
    starting = _von_proc is not None and _von_proc.poll() is None and health is None
    failed = _von_proc is not None and _von_proc.poll() is not None and health is None
    state = {
        "url": VON_BASE_URL,
        "running": health is not None,
        "version": (health or {}).get("engine") or (health or {}).get("version"),
        "can_start": bool(VON_BIN) and host in ("127.0.0.1", "localhost", "::1"),
        "starting": starting,
        "log": _von_log,
    }
    if failed:
        tail = ""
        try:
            tail = Path(_von_log).read_text(errors="replace")[-1500:]
        except OSError:
            pass
        state["error"] = f"von serve exited with code {_von_proc.returncode}.\n{tail}".strip()
    return state


def start_von():
    """Spawn `von serve` on VON_BASE_URL's host and port. Returns (http_status, body)."""
    global _von_proc, _von_log
    with _von_lock:
        state = von_state()
        if state["running"] or state["starting"]:
            return 200, state
        if not state["can_start"]:
            if not VON_BIN:
                return 400, {"error": "Von is not installed. Run: uv venv --python 3.12 ~/.venvs/von && uv pip install --python ~/.venvs/von/bin/python 'von-sdk>=1.3.7'"}
            return 400, {"error": f"VON_BASE_URL is {VON_BASE_URL}, which is not on this machine, so it cannot be started from here."}
        parts = urllib.parse.urlsplit(VON_BASE_URL)
        fd, _von_log = tempfile.mkstemp(prefix="von-serve-", suffix=".log")
        log = os.fdopen(fd, "wb")
        try:
            _von_proc = subprocess.Popen(
                [VON_BIN, "serve", "--host", parts.hostname, "--port", str(parts.port or 8000)],
                stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
            )
        except OSError as err:
            return 500, {"error": f"Could not run {VON_BIN}: {err}"}
        finally:
            log.close()
        atexit.register(stop_von)
        print(f"Started von serve (pid {_von_proc.pid}), log at {_von_log}")
        return 202, von_state()


def stop_von():
    """Stop the `von serve` child when the app server exits, so it lives for this session only."""
    if _von_proc is not None and _von_proc.poll() is None:
        _von_proc.terminate()
        try:
            _von_proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            _von_proc.kill()


def call_von(base_url, api_key, model, state, questions):
    """POST one System One request to a Von server. Returns (http_status, parsed_body).

    An unreachable server returns (502, {"error": ..., "unreachable": True}).
    """
    url = base_url.rstrip("/") + "/v1/systemone"
    headers = {"Content-Type": "application/json", "Accept": "application/json", "User-Agent": "von-router/1.0"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    payload = json.dumps({"model": model, "state": state, "questions": questions}).encode()
    req = urllib.request.Request(url, data=payload, method="POST", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            status, raw = resp.status, resp.read()
    except urllib.error.HTTPError as err:
        status, raw = err.code, err.read()
    except (urllib.error.URLError, TimeoutError, OSError) as err:
        return 502, {"error": f"Could not reach the Von server at {base_url}: {err}. Start it with `von serve`.", "unreachable": True}
    try:
        return status, json.loads(raw)
    except ValueError:
        return status, {"error": raw.decode("utf-8", "replace")[:2000]}


class Handler(BaseHTTPRequestHandler):
    def _send(self, status, body, content_type="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _read_json(self):
        """Validate a same-origin JSON post. Returns the parsed body, or None after replying."""
        host = self.headers.get("Host", "")
        origin = self.headers.get("Origin")
        if origin and origin != f"http://{host}":
            self._send(403, {"error": "Cross-origin requests are not allowed."})
            return None
        if "application/json" not in self.headers.get("Content-Type", ""):
            self._send(415, {"error": "Send JSON."})
            return None
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0 or length > MAX_BODY:
            self._send(413, {"error": "Request body is empty or too large."})
            return None
        try:
            body = json.loads(self.rfile.read(length))
        except ValueError:
            self._send(400, {"error": "Request body is not valid JSON."})
            return None
        if not isinstance(body, dict):
            self._send(400, {"error": "Request body must be a JSON object."})
            return None
        return body

    def do_GET(self):
        if self.path.split("?")[0] in ("/", "/index.html"):
            self._send(200, INDEX.read_bytes(), "text/html; charset=utf-8")
        elif self.path == "/api/config":
            self._send(200, {
                "von_url": VON_BASE_URL,
                "von_env_key": bool(os.environ.get("VON_API_KEY")),
                "anthropic_env_key": bool(os.environ.get("ANTHROPIC_API_KEY")),
            })
        elif self.path == "/api/von":
            self._send(200, von_state())
        else:
            self._send(404, {"error": "Not found"})

    def do_POST(self):
        if self.path == "/api/classify":
            return self.classify()
        if self.path == "/api/answer":
            return self.answer()
        if self.path == "/api/von/start":
            return self.von_start()
        self._send(404, {"error": "Not found"})

    def von_start(self):
        host = self.headers.get("Host", "")
        origin = self.headers.get("Origin")
        if origin and origin != f"http://{host}":
            return self._send(403, {"error": "Cross-origin requests are not allowed."})
        status, body = start_von()
        self._send(status, body)

    def classify(self):
        body = self._read_json()
        if body is None:
            return
        base_url = str(body.get("von_url") or VON_BASE_URL).strip()
        parts = urllib.parse.urlsplit(base_url)
        if parts.scheme not in ("http", "https") or not parts.netloc:
            return self._send(400, {"error": "The Von server address must be an http or https URL, such as http://127.0.0.1:8000."})
        api_key = (body.get("api_key") or os.environ.get("VON_API_KEY") or "").strip()
        questions = body.get("questions")
        if not isinstance(questions, dict) or not questions:
            return self._send(400, {"error": "Primitives must be a non-empty JSON object."})
        if not body.get("state"):
            return self._send(400, {"error": "The coding request is empty."})
        status, result = call_von(base_url, api_key, body.get("model") or "von-latest", body["state"], questions)
        reply = {"status": status, "ok": 200 <= status < 300, "result": result}
        if isinstance(result, dict) and result.pop("unreachable", False):
            reply["unreachable"] = True
        self._send(200, reply)

    def answer(self):
        """Forward one streaming Messages request and pipe the SSE bytes back unchanged."""
        body = self._read_json()
        if body is None:
            return
        api_key = (body.get("api_key") or os.environ.get("ANTHROPIC_API_KEY") or "").strip()
        if not api_key:
            return self._send(400, {"error": "Enter an Anthropic API key, or set ANTHROPIC_API_KEY before starting the app."})
        req_body = body.get("body")
        if not isinstance(req_body, dict) or req_body.get("model") not in ALLOWED_MODELS:
            return self._send(400, {"error": "The request body is missing or names an unknown model."})
        req_body["stream"] = True
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            "User-Agent": "von-router/1.0",
        }
        if "fallbacks" in req_body:
            headers["anthropic-beta"] = "server-side-fallback-2026-07-01"
        req = urllib.request.Request(ANTHROPIC_URL, data=json.dumps(req_body).encode(), method="POST", headers=headers)
        try:
            upstream = urllib.request.urlopen(req, timeout=600)
        except urllib.error.HTTPError as err:
            raw = err.read()
            try:
                result = json.loads(raw)
            except ValueError:
                result = {"error": raw.decode("utf-8", "replace")[:2000]}
            return self._send(err.code, {"status": err.code, "result": result})
        except (urllib.error.URLError, TimeoutError) as err:
            return self._send(502, {"error": f"Could not reach the Anthropic API: {err}"})

        # HTTP/1.0 responses end when the connection closes, so no framing is needed.
        self.send_response(upstream.status)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        with upstream:
            try:
                while True:
                    chunk = upstream.read1(4096) if hasattr(upstream, "read1") else upstream.read(4096)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass  # the browser went away mid-stream

    def log_message(self, fmt, *args):  # request bodies carry keys; log paths only
        print(f"{self.command} {self.path.split('?')[0]} -> {args[1] if len(args) > 1 else ''}")


def main():
    parser = argparse.ArgumentParser(description="Local web app that routes coding requests to Claude via Von.")
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Von Semantic Router is at http://127.0.0.1:{args.port}  (Ctrl+C to stop)")
    if von_health(VON_BASE_URL):
        print(f"Von is running at {VON_BASE_URL}")
    elif VON_BIN:
        print(f"Von is not running at {VON_BASE_URL}; the page's Start button runs {VON_BIN}")
    else:
        print(f"Von is expected at {VON_BASE_URL}  (pip install von-sdk, then von serve)")
    # A plain SIGTERM would skip the cleanup below, leaving `von serve` running.
    def on_term(*_):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, on_term)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print()
    finally:
        stop_von()


if __name__ == "__main__":
    main()
