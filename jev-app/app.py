#!/usr/bin/env python3
"""Jev Runner: a tiny local web app for TypeSafe's Jev (System One) model.

Run:   python3 app.py            then open http://127.0.0.1:8765
Needs: Python 3.8+, no third-party packages.

The browser cannot call api.typesafe.ai directly (the API rejects cross-origin
requests), so this server serves the form and forwards each run to the API.
The API key is sent with each run and is never written to disk. If the key
field is left empty, the TYPESAFE_API_KEY environment variable is used.
"""
import argparse
import json
import os
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

API_URL = os.environ.get("TYPESAFE_API_URL", "https://api.typesafe.ai/v1/systemone")
# The same page is published on the site as /jev.html.
INDEX = Path(__file__).resolve().parent.parent / "public" / "jev.html"
MAX_BODY = 2 * 1024 * 1024


def call_jev(api_key, model, state, questions):
    """POST one request to the Jev API. Returns (http_status, parsed_body)."""
    payload = json.dumps({"model": model, "state": state, "questions": questions}).encode()
    req = urllib.request.Request(
        API_URL,
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "jev-runner/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            status, raw = resp.status, resp.read()
    except urllib.error.HTTPError as err:
        status, raw = err.code, err.read()
    except (urllib.error.URLError, TimeoutError) as err:
        return 502, {"error": f"Could not reach the Jev API: {err}"}
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

    def do_GET(self):
        if self.path.split("?")[0] in ("/", "/index.html"):
            self._send(200, INDEX.read_bytes(), "text/html; charset=utf-8")
        elif self.path == "/api/config":
            self._send(200, {"env_key": bool(os.environ.get("TYPESAFE_API_KEY"))})
        else:
            self._send(404, {"error": "Not found"})

    def do_POST(self):
        if self.path != "/api/run":
            return self._send(404, {"error": "Not found"})
        # Only accept same-origin JSON posts, so other websites open in the
        # browser cannot drive this local server.
        host = self.headers.get("Host", "")
        origin = self.headers.get("Origin")
        if origin and origin not in (f"http://{host}",):
            return self._send(403, {"error": "Cross-origin requests are not allowed."})
        if "application/json" not in self.headers.get("Content-Type", ""):
            return self._send(415, {"error": "Send JSON."})
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0 or length > MAX_BODY:
            return self._send(413, {"error": "Request body is empty or too large."})
        try:
            body = json.loads(self.rfile.read(length))
        except ValueError:
            return self._send(400, {"error": "Request body is not valid JSON."})

        api_key = (body.get("api_key") or os.environ.get("TYPESAFE_API_KEY") or "").strip()
        questions = body.get("questions")
        if not api_key:
            return self._send(400, {"error": "Enter an API key, or set TYPESAFE_API_KEY before starting the app."})
        if not isinstance(questions, dict) or not questions:
            return self._send(400, {"error": "Primitives must be a non-empty JSON object."})
        if body.get("state") in (None, "", {}, []):
            return self._send(400, {"error": "State is empty."})

        status, result = call_jev(api_key, body.get("model") or "jev-latest", body["state"], questions)
        self._send(200, {"status": status, "ok": 200 <= status < 300, "result": result})

    def log_message(self, fmt, *args):  # request bodies carry the key; log paths only
        print(f"{self.command} {self.path.split('?')[0]} -> {args[1] if len(args) > 1 else ''}")


def main():
    parser = argparse.ArgumentParser(description="Local web app for running TypeSafe Jev.")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Jev Runner is at http://127.0.0.1:{args.port}  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print()


if __name__ == "__main__":
    main()
