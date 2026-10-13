#!/usr/bin/env python3
"""Jev Semantic Router: a tiny local web app that routes coding requests to Claude.

Run:   python3 router.py          then open http://127.0.0.1:8766
Needs: Python 3.8+, no third-party packages.

The page (public/jev-router.html) asks TypeSafe's Jev model how hard a coding
request is, picks the cheapest Claude tier (Haiku, Sonnet, Opus) whose
cumulative probability reaches the coverage threshold, and streams that
model's answer. This server serves the page and forwards both calls, because
the browser cannot call api.typesafe.ai directly. Keys are sent with each
request and never written to disk. Empty key fields fall back to the
TYPESAFE_API_KEY and ANTHROPIC_API_KEY environment variables.

The same page is published at https://rajatghosh.me/jev-router.html, where
the Jev call goes through the relay in relay/ and the Claude call goes from
the browser straight to api.anthropic.com.
"""
import argparse
import json
import os
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from app import call_jev

ANTHROPIC_URL = os.environ.get("ANTHROPIC_API_URL", "https://api.anthropic.com/v1/messages")
INDEX = Path(__file__).resolve().parent.parent / "public" / "jev-router.html"
MAX_BODY = 2 * 1024 * 1024
ALLOWED_MODELS = {"claude-haiku-5-5", "claude-sonnet-5-5", "claude-opus-5-5"}


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
                "typesafe_env_key": bool(os.environ.get("TYPESAFE_API_KEY")),
                "anthropic_env_key": bool(os.environ.get("ANTHROPIC_API_KEY")),
            })
        else:
            self._send(404, {"error": "Not found"})

    def do_POST(self):
        if self.path == "/api/classify":
            return self.classify()
        if self.path == "/api/answer":
            return self.answer()
        self._send(404, {"error": "Not found"})

    def classify(self):
        body = self._read_json()
        if body is None:
            return
        api_key = (body.get("api_key") or os.environ.get("TYPESAFE_API_KEY") or "").strip()
        if not api_key:
            return self._send(400, {"error": "Enter a TypeSafe API key, or set TYPESAFE_API_KEY before starting the app."})
        questions = body.get("questions")
        if not isinstance(questions, dict) or not questions:
            return self._send(400, {"error": "Primitives must be a non-empty JSON object."})
        if not body.get("state"):
            return self._send(400, {"error": "The coding request is empty."})
        status, result = call_jev(api_key, body.get("model") or "jev-latest", body["state"], questions)
        self._send(200, {"status": status, "ok": 200 <= status < 300, "result": result})

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
            "User-Agent": "jev-router/1.0",
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
    parser = argparse.ArgumentParser(description="Local web app that routes coding requests to Claude via Jev.")
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Jev Semantic Router is at http://127.0.0.1:{args.port}  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print()


if __name__ == "__main__":
    main()
