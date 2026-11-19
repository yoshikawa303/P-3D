# Codex / Agent Entry Rules

<!-- AIDESK:SHARED:BEGIN v1 （この枠は AIDESK が更新する。形式を手で変えない） -->
## 共有ルール（全プロジェクト共通・AIDESK が更新する）

- 本書は Codex / ChatGPT / Gemini 用の入口。**主入口は `CLAUDE.md`**（共有ルールとプロジェクト固有ルールの両方がある）。矛盾した場合は `CLAUDE.md` を正とし、同じ作業内で両方を直す。
- **この枠の外はプロジェクト固有**。共有部の形式（マーカー行・見出し・箇条書き）を手で変えない。共有部は AIDESK（`aidesk rules`）が更新する。
- 最初に `CLAUDE.md` と `ai/HANDOFF.md` を読む。作業終了時は `ai/HANDOFF.md` を上書きし、作業履歴を `Docs/CHAT_WORK_LOG_<その週の月曜 YYMMDD>.md` に追記する。
- 論理単位ごとにローカルコミットする。完了前にビルド・テストを自分で実行して結果を記録する。仕様・データ形式・API・外部公開の変更は実装前に確認する。秘密情報を書かない。
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
