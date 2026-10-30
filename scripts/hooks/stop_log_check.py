#!/usr/bin/env python3
"""Stop フック — セッション終了時に CHAT_WORK_LOG の記録漏れを検査する（claude-harness）。

今週のログに本日付のエントリが1件も無い場合のみ exit 2 で終了を保留し、記録を促す。
stop_hook_active が立っている場合（このフック起因の継続中）は何もしない（無限ループ防止）。
"""
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from worklog_path import worklog_path  # noqa: E402


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}
    if payload.get("stop_hook_active"):
        return

    try:
        os.chdir(os.environ.get("CLAUDE_PROJECT_DIR") or ".")
    except Exception:
        return

    log = worklog_path()
    today = datetime.date.today().strftime("%Y-%m-%d")

    if not os.path.isfile(log):
        sys.stderr.write(
            f"[harness/Stop] §2.1: 今週のチャット作業ログ {log} が存在しません。"
            "「種別: 依頼内容/作業結果」を記録してから終了してください。\n")
        sys.exit(2)

    try:
        with open(log, encoding="utf-8") as f:
            body = f.read()
    except Exception:
        return

    if f"### {today}" not in body:
        sys.stderr.write(
            f"[harness/Stop] §2.1: {log} に本日 ({today}) のエントリがありません。"
            "「種別: 依頼内容/作業結果」を記録してから終了してください。\n")
        sys.exit(2)


if __name__ == "__main__":
    main()
