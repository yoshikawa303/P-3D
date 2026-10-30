#!/usr/bin/env python3
"""品質計測ハーネス用ローカルサーバー。静的配信に加え、POST /save/<相対パス> で Docs/QC/ImageQuality 配下へ保存する。"""
import base64, http.server, json, os, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "Docs" / "QC" / "ImageQuality"


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(ROOT), **k)

    def do_POST(self):
        if not self.path.startswith("/save/"):
            self.send_error(404)
            return
        rel = pathlib.PurePosixPath(self.path[len("/save/"):])
        target = (OUT / rel).resolve()
        if OUT.resolve() not in target.parents:
            self.send_error(400)
            return
        body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        target.parent.mkdir(parents=True, exist_ok=True)
        if self.headers.get("X-Encoding") == "dataurl":
            body = base64.b64decode(body.split(b",", 1)[1])
        target.write_bytes(body)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8140
    http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
