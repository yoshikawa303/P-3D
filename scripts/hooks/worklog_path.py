#!/usr/bin/env python3
"""今週の CHAT_WORK_LOG 相対パスを表示する（CLAUDE.md §2.1 のファイル選択規則）。

- main 系ブランチ: Docs/CHAT_WORK_LOG_<週の月曜YYMMDD>.md
- DebugRelease 系ブランチ: Docs/CHAT_WORK_LOG_DebugRelease_<週の月曜YYMMDD>.md
"""
import datetime
import subprocess


def worklog_path() -> str:
    try:
        branch = subprocess.run(
            ["git", "symbolic-ref", "--short", "-q", "HEAD"],
            capture_output=True, text=True, timeout=5,
        ).stdout.strip() or "unknown"
    except Exception:
        branch = "unknown"
    today = datetime.date.today()
    monday = (today - datetime.timedelta(days=today.weekday())).strftime("%y%m%d")
    if "DebugRelease" in branch:
        return f"Docs/CHAT_WORK_LOG_DebugRelease_{monday}.md"
    return f"Docs/CHAT_WORK_LOG_{monday}.md"


if __name__ == "__main__":
    print(worklog_path())
