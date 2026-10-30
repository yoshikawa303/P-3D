#!/usr/bin/env bash
# claude-harness セットアップランチャ（ダブルクリック実行用）
#
# 使い方A（プロジェクト直下に置いて実行）:
#   このファイルを対象プロジェクトのルートフォルダへコピーし、Finder でダブルクリック
#   → このファイルが置かれているフォルダへハーネスを適用する。
#
# 使い方B（フォルダを選んで実行）:
#   maruPlay リポジトリ内やデスクトップに置いたままダブルクリック
#   → フォルダ選択ダイアログが開くので、適用先プロジェクトのルートを選ぶ。
#
# 実体は Tools/claude-harness/install.sh（冪等・再実行安全）。
set -uo pipefail

HARNESS_SRC="/Volumes/DATA/XCode_Project/maruPlay-main/Tools/claude-harness"
SELF_DIR="$(cd "$(dirname "$0")" && pwd)"

finish() {
  echo
  echo "Enter キーでこのウィンドウを閉じられます..."
  read -r || true
  exit "${1:-0}"
}

fail() {
  echo
  echo "[claude-harness] エラー: $1"
  finish 1
}

[ -f "$HARNESS_SRC/install.sh" ] || fail "ハーネス原本が見つかりません: $HARNESS_SRC
（maruPlay リポジトリの場所を移動した場合は、このファイル冒頭の HARNESS_SRC を修正してください）"

TARGET="$SELF_DIR"
case "$SELF_DIR" in
  /Volumes/DATA/XCode_Project/maruPlay-main*|"$HOME/Desktop"*)
    # 原本リポジトリ内・デスクトップから起動された場合は、適用先をダイアログで選択する
    echo "[claude-harness] 適用先プロジェクトのルートフォルダを選択してください（ダイアログ表示中）..."
    TARGET="$(osascript -e 'POSIX path of (choose folder with prompt "claude-harness を適用するプロジェクトのルートフォルダを選択してください")' 2>/dev/null || true)"
    [ -n "$TARGET" ] || fail "フォルダが選択されませんでした（キャンセル）"
    ;;
esac

echo "[claude-harness] 適用先: $TARGET"

# 誤適用防止セーフガード: プロジェクトルートらしくないフォルダには確認を挟む
if [ ! -f "$TARGET/CLAUDE.md" ] && [ ! -e "$TARGET/.git" ]; then
  echo
  echo "[claude-harness] 注意: このフォルダには CLAUDE.md も .git も見つかりません。"
  echo "  適用先は通常「CLAUDE.md のあるプロジェクトのルートフォルダ」です。"
  printf '  それでもこのフォルダへ適用しますか？ [y/N]: '
  read -r ANS || ANS=""
  # 全角入力（日本語IME確定時の ｙ/Ｙ 等）も許容する
  ANS="$(printf '%s' "$ANS" | tr 'ｙＹ' 'yY' | tr -d '[:space:]')"
  case "$ANS" in
    y|Y|yes|YES|はい) : ;;
    *) fail "キャンセルしました（正しいプロジェクトルートで再実行してください）" ;;
  esac
fi

echo
if bash "$HARNESS_SRC/install.sh" "$TARGET"; then
  echo
  echo "[claude-harness] セットアップ完了。"
  echo "  1. 対象プロジェクトで Claude Code セッションを再起動してください。"
  echo "  2. 対象プロジェクトの CLAUDE.md へスキル参照の1文を追記してください（README 参照）。"
else
  fail "インストールに失敗しました（上のメッセージを確認してください）"
fi
finish 0
