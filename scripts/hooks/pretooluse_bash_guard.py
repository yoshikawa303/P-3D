#!/usr/bin/env python3
"""PreToolUse(Bash) ガード — CLAUDE.md §2.3 / §4 / §4.1 の注意書きを実行前の決定的チェックへ置き換える（claude-harness）。

違反時は exit 2 でツール実行をブロックし、stderr の理由が AI へ返る。
"""
import json
import os
import re
import subprocess
import sys


def deny(msg: str) -> None:
    sys.stderr.write(msg + "\n")
    sys.exit(2)


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return
    if payload.get("tool_name") != "Bash":
        return
    cmd = (payload.get("tool_input") or {}).get("command") or ""
    if not cmd:
        return

    # §4.1 / §2.3: シミュレータの手動確認用データを消す操作は禁止
    if re.search(r"\brm\b[^\n|;&]*CoreSimulator/Devices", cmd):
        deny("[harness/PreToolUse] §4.1: ~/Library/Developer/CoreSimulator/Devices は削除対象外です"
             "（手動確認用のアプリ内データが消えるため）。scripts/dev/clean_dev_temp.sh を使ってください。")
    if re.search(r"simctl\s+erase\b", cmd):
        deny("[harness/PreToolUse] §2.3: `simctl erase` は手動確認用のアプリ内データが消えるため実施しないでください"
             "（クローン失敗時は ~/Library/Logs/CoreSimulator/CoreSimulator.log で切り分ける）。")

    if "xcodebuild" not in cmd:
        return

    # §2.3: xcodebuild ... test は -parallel-testing-enabled NO 必須
    if re.search(r"(^|\s)test(\s|$)", cmd) and "-parallel-testing-enabled NO" not in cmd:
        deny("[harness/PreToolUse] §2.3: `xcodebuild ... test` には `-parallel-testing-enabled NO` が必須です"
             "（XCTestDevices クローン失敗で1件も実行されない事故の防止）。フラグを追加して再実行してください。")

    # §4: xcode-select が CommandLineTools を指す環境では DEVELOPER_DIR の明示が必要
    if "DEVELOPER_DIR" not in cmd and not os.environ.get("DEVELOPER_DIR"):
        try:
            p = subprocess.run(["xcode-select", "-p"], capture_output=True, text=True, timeout=5)
            if "CommandLineTools" in (p.stdout or ""):
                deny("[harness/PreToolUse] §4: xcode-select が CommandLineTools を指しています。"
                     "`DEVELOPER_DIR=<Xcode.app>/Contents/Developer` を先頭に付けて実行してください。")
        except Exception:
            pass

    # §2: build/test では Derived Data の置き場を明示する
    if re.search(r"\s-scheme\s", cmd) and "-derivedDataPath" not in cmd:
        deny("[harness/PreToolUse] §2: `xcodebuild` の build/test では `-derivedDataPath` で Derived Data 置き場を"
             "明示してください（ワークツリー残置・起動ディスク圧迫の防止）。")


if __name__ == "__main__":
    main()
