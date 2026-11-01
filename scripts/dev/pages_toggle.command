#!/bin/bash
# P-3D: GitHub Pages 一時公開の切替（Mac ダブルクリック用）。
# Private なら Public にして Pages へ main を配信、Public なら Private に戻す。詳細は pages_toggle.py。
cd "$(dirname "$0")" || exit 1
python3 pages_toggle.py "$@"
echo
read -n 1 -r -s -p "何かキーを押すと閉じます"
echo
