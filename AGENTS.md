# Codex / Agent Entry Rules

対象: Codexおよび `AGENTS.md` を入口として読むAI。

1. 作業開始前に `CLAUDE.md` を全文確認し、共通運用ルールに従う。
2. 次に `PROJECT_RULES.md`、`Docs/ARCHITECTURE.md`、`CHANGELOG.md`、対象週の `Docs/CHAT_WORK_LOG_<YYMMDD>.md` を確認する。
3. バグ修正は根本原因と回帰検査を確認し、デスクトップ確認とiPhone Safari実機確認を区別する。
4. 論理単位ごとにcommit／pushする。Git checkoutでない場合は無断で `git init` せず、制約を記録する。
5. 作業前後に使用モデル、理由、動的切替、検証、commit／push結果をチャットと作業ログへ記録する。

詳細と正本は `CLAUDE.md` と `PROJECT_RULES.md` とする。

