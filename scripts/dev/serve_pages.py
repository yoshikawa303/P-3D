#!/usr/bin/env python3
"""GitHub Pages相当のローカル配信: https://localhost:8443/P-3D/ でリポジトリ直下を配信する。

Pagesと同じく /P-3D/ 配下の相対URLで動作する。既定は自分のMacだけ（127.0.0.1）に公開する。
iPhone Safari実機で確認する場合のみ --lan を付ける（同一Wi-Fi内へ公開される）。
HTTPS（自己署名証明書、.tmp/ に生成）で配信するため、iPhone Safariでもカメラ権限を要求できる。
使い方: python3 scripts/dev/serve_pages.py [--port 8443] [--lan] [--http]
"""
import argparse, functools, http.server, socket, ssl, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PREFIX = "/P-3D/"


class Handler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        if path == "/P-3D":
            path = PREFIX
        if not path.startswith(PREFIX):
            return str(ROOT / "__not_found__")
        return super().translate_path("/" + path[len(PREFIX):])

    def end_headers(self):
        self.send_header("Cache-Control", "max-age=0, no-cache")
        super().end_headers()


def lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def ensure_cert(ip):
    d = ROOT / ".tmp" / "local-cert"
    d.mkdir(parents=True, exist_ok=True)
    cert, key = d / f"{ip}.crt", d / f"{ip}.key"
    if not cert.exists():
        subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "30",
                        "-keyout", str(key), "-out", str(cert), "-subj", "/CN=P-3D local",
                        "-addext", f"subjectAltName=IP:{ip},IP:127.0.0.1,DNS:localhost"],
                       check=True, capture_output=True)
    return cert, key


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8443)
    ap.add_argument("--lan", action="store_true", help="同一Wi-Fiへ公開する（iPhone実機用）")
    ap.add_argument("--http", action="store_true", help="HTTPSを使わない（iPhoneのカメラは使えない）")
    a = ap.parse_args()
    ip = lan_ip() if a.lan else "127.0.0.1"
    server = http.server.ThreadingHTTPServer(("0.0.0.0" if a.lan else "127.0.0.1", a.port),
                                             functools.partial(Handler, directory=str(ROOT)))
    scheme = "http"
    if not a.http:
        cert, key = ensure_cert(ip)
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(cert, key)
        server.socket = ctx.wrap_socket(server.socket, server_side=True)
        scheme = "https"
    print(f"Mac: {scheme}://localhost:{a.port}{PREFIX}")
    if a.lan:
        print(f"iPhone: {scheme}://{ip}:{a.port}{PREFIX}  (自己署名証明書の警告を許可して開く)")
    server.serve_forever()


if __name__ == "__main__":
    main()
