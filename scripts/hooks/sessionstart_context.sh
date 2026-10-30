#!/usr/bin/env bash
# SessionStart フック — セッション冒頭へ動的コンテキストを注入する（claude-harness）。
# CLAUDE.md §2.1 の週次ログファイル名・現在バージョンを機械側で確定し、AI の計算ミスを防ぐ。
set -uo pipefail
cd "${CLAUDE_PROJECT_DIR:-.}" 2>/dev/null || exit 0
HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

BRANCH="$(git symbolic-ref --short -q HEAD 2>/dev/null)"
[ -n "$BRANCH" ] || BRANCH=unknown
LOG="$(python3 "$HOOK_DIR/worklog_path.py" 2>/dev/null || echo 'Docs/CHAT_WORK_LOG_unknown.md')"
NOTE=""
[ -f "$LOG" ] || NOTE="（未作成。最初の記録時に新規作成する）"

PBX="$(ls -d ./*.xcodeproj/project.pbxproj 2>/dev/null | head -1)"
MV=""
CPV=""
if [ -n "$PBX" ]; then
  MV="$(grep -m1 -o 'MARKETING_VERSION = [^;]*' "$PBX" 2>/dev/null | sed 's/.*= //')"
  CPV="$(grep -m1 -o 'CURRENT_PROJECT_VERSION = [^;]*' "$PBX" 2>/dev/null | sed 's/.*= //')"
fi
[ -n "$MV" ] || MV="?"
[ -n "$CPV" ] || CPV="?"

cat <<EOF
[harness/SessionStart] branch=${BRANCH} / 今週のチャット作業ログ: ${LOG}${NOTE}
[harness/SessionStart] MARKETING_VERSION=${MV} / CURRENT_PROJECT_VERSION=${CPV}（表示リリース番号 v${MV} (beta Build ${CPV})）
[harness/SessionStart] リマインダ: 依頼受付時は他のツール実行より先に上記ログへ「種別: 依頼内容」を追記し、§2.6 のモデル/工数宣言を行う。規約の詳細手順は .claude/skills/ の該当スキルをロードする。
EOF
exit 0
