#!/usr/bin/env python3
"""OpenPushups server: serves the app and persists its state.

GET  /api/data  -> data/data.json (or {} if none yet)
PUT  /api/data  -> validate JSON body, write atomically to data/data.json
Everything else is served as static files from the app directory.
Python stdlib only.
"""
import json
import os
import tempfile
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT, "data")
DATA_FILE = os.path.join(DATA_DIR, "data.json")
MAX_BODY = 5 * 1024 * 1024


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def send_json(self, code, body):
        data = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/api/data":
            try:
                with open(DATA_FILE, encoding="utf-8") as f:
                    self.send_json(200, f.read())
            except FileNotFoundError:
                self.send_json(200, "{}")
            return
        super().do_GET()

    def do_PUT(self):
        if self.path != "/api/data":
            self.send_json(404, '{"error":"not found"}')
            return
        length = int(self.headers.get("Content-Length") or 0)
        if not 0 < length <= MAX_BODY:
            self.send_json(413, '{"error":"bad content length"}')
            return
        raw = self.rfile.read(length)
        try:
            json.loads(raw)
        except ValueError:
            self.send_json(400, '{"error":"invalid json"}')
            return
        os.makedirs(DATA_DIR, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=DATA_DIR, suffix=".tmp")
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(raw)
            os.replace(tmp, DATA_FILE)
        except BaseException:
            os.unlink(tmp)
            raise
        self.send_json(200, '{"ok":true}')


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
