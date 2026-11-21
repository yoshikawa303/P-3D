# Codex / Agent Entry Rules

<!-- AIDESK:SHARED:BEGIN v3 （この枠は AIDESK が更新する。形式を手で変えない） -->
## 共有ルール（全プロジェクト共通・AIDESK が更新する）

- 本書は Codex / ChatGPT / Gemini / Grok 用の入口。**主入口は `CLAUDE.md`**（共有ルールとプロジェクト固有ルールの両方がある）。矛盾した場合は `CLAUDE.md` を正とし、同じ作業内で両方を直す。
- **この枠の外はプロジェクト固有**。共有部の形式（マーカー行・見出し・箇条書き）を手で変えない。共有部は AIDESK（`aidesk rules`）が更新する。
- 最初に `CLAUDE.md` を読み、そこで指定された文書（`ai/` を運用している場合は `ai/HANDOFF.md` を含む）を読む。作業終了時は、`ai/` を運用していれば `ai/HANDOFF.md` を上書きし、作業履歴を `Docs/CHAT_WORK_LOG_<その週の月曜 YYMMDD>.md` に追記する（書式は `CLAUDE.md` の共有部に従う）。
- 依頼を記録する時は、依頼 ID `R<YYMMDD>-<NN>`（依頼日 JST＋その日の連番）を採番して見出しの表題の先頭に `[R…]` と付け、同じ依頼の結果・QC・コミット本文（`Request: R…`）にも使う。指示の先頭にフラグ記号が無ければ実行中 AI の記号（Claude=★ / ChatGPT・Codex=☆ / Gemini=✦ / Grok=✧）を項目ごとの先頭へ足す。記号以外は原文を変えない。
- 論理単位ごとにコミットし、**必ず続けて push する**（push できない時は理由・未 push コミット・次の操作を記録する）。完了前にビルド・テストを自分で実行して結果を記録する。仕様・ユーザー向け機能・データ形式・API・外部公開の変更は実装前に確認する。原因確認前に表面的な修正をしない。バグ修正は修正前 FAIL・修正後 PASS のテストを足す。レビューは新規指摘 0 件まで繰り返し（上限 20 回）、結果を回ごとの表で残す。着手前に工程別のモデル/工数を宣言し、完了時に使用モデルを報告する。最終返信にバージョン情報を書く。秘密情報を書かない。
<!-- AIDESK:SHARED:END -->

<!-- AIDESK:PROJECT:BEGIN （以下はプロジェクト固有。AIDESK は触らない） -->

対象: Codexおよび `AGENTS.md` を入口として読むAI。

1. 作業開始前に `CLAUDE.md` を全文確認し、共通運用ルールに従う。
2. 次に `PROJECT_RULES.md`、`Docs/ARCHITECTURE.md`、`CHANGELOG.md`、対象週の `Docs/CHAT_WORK_LOG_<YYMMDD>.md` を確認する。
3. バグ修正は根本原因と回帰検査を確認し、デスクトップ確認とiPhone Safari実機確認を区別する。
4. 論理単位ごとにcommit／pushする。Git checkoutでない場合は無断で `git init` せず、制約を記録する。
5. 作業前後に使用モデル、理由、動的切替、検証、commit／push結果をチャットと作業ログへ記録する。

詳細と正本は `CLAUDE.md` と `PROJECT_RULES.md` とする。

<!-- AIDESK:PROJECT:END -->
