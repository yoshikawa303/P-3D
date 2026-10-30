#!/usr/bin/env bash
# claude-harness アンインストールランチャ（ダブルクリック実行用・誤適用の解除）
#
# 使い方A: 誤って適用したフォルダへこのファイルをコピーしてダブルクリック → その場所から解除。
# 使い方B: maruPlay リポジトリ内やデスクトップからダブルクリック → フォルダ選択ダイアログで解除先を選ぶ。
#
# 実体は Tools/claude-harness/uninstall.sh（ハーネス配布物と同名のファイルだけを除去。
# プロジェクト固有のスキル・設定・ソースには触れない）。
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

[ -f "$HARNESS_SRC/uninstall.sh" ] || fail "ハーネス原本が見つかりません: $HARNESS_SRC"

TARGET="$SELF_DIR"
case "$SELF_DIR" in
  /Volumes/DATA/XCode_Project/maruPlay-main*|"$HOME/Desktop"*)
    echo "[claude-harness] 解除するプロジェクトのフォルダを選択してください（ダイアログ表示中）..."
    TARGET="$(osascript -e 'POSIX path of (choose folder with prompt "claude-harness を解除（アンインストール）するフォルダを選択してください")' 2>/dev/null || true)"
    [ -n "$TARGET" ] || fail "フォルダが選択されませんでした（キャンセル）"
    ;;
esac

echo "[claude-harness] 解除対象: $TARGET"
printf 'このフォルダから claude-harness を取り除きます。よろしいですか？ [y/N]: '
read -r ANS || ANS=""
# 全角入力（日本語IME確定時の ｙ/Ｙ 等）も許容する
ANS="$(printf '%s' "$ANS" | tr 'ｙＹ' 'yY' | tr -d '[:space:]')"
case "$ANS" in
  y|Y|yes|YES|はい) : ;;
  *) fail "キャンセルしました" ;;
esac
echo

if bash "$HARNESS_SRC/uninstall.sh" "$TARGET"; then
  echo
  echo "[claude-harness] 解除が完了しました。"
else
  fail "アンインストールに失敗しました（上のメッセージを確認してください）"
fi
finish 0
