#!/bin/bash
# P-3Dをローカル確認用HTTPサーバーで起動し、ブラウザで開く(ダブルクリック可)。
# デモ画像・カメラは file:// では動かないため、必ずこのHTTP経由で開く。終了は Ctrl+C。
cd "$(dirname "$0")/../.." || exit 1
PORT=8765
while lsof -iTCP:$PORT -sTCP:LISTEN >/dev/null 2>&1; do PORT=$((PORT+1)); done
URL="http://127.0.0.1:$PORT/index.html"
echo "P-3D ローカルサーバー: $URL (Ctrl+Cで終了)"
(sleep 1; open "$URL") &
exec python3 -m http.server "$PORT" --bind 127.0.0.1
