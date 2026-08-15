# Chat Work Log

## 2026-08-15

### 2026-08-15 19:07 JST - Codex GPT-5 - 種別: 依頼内容 - Pages公開版の顔追跡修正と開発規則移植

- 内容:

  ```text
  ★現状はSafariでページ表示する為、Pages機能はPublicで動作しています。
  ★コーディング、チャット履歴保存、git管理など開発で共有可能な運用ルールをmaruPlayプロジェクトのClaude.md、Agent.md、Gemin.mdなどにインポートして。
  ★バグ：https://yoshikawa303.github.io/P-3D/ にPages公開設定を行って動作確認しましたが、フロントカメラを押しても認識せず必ず手動になる。
  ```

### 2026-08-15 19:07 JST - Codex GPT-5 - 種別: 経過 - 使用モデルと根本原因

- 内容:

  使用モデルはGPT-5系Codexを継続。ブラウザ互換性の根本原因調査、実装、回帰検査、運用規則の移植を一貫して扱うため。モデルを動的に切り替える権限はなく、切替なし。

  公開版とローカル`index.html`のGit blob SHAが一致することを確認。ボタン押下後に`Failed to fetch dynamically imported module`を再現し、参照中の`@mediapipe/tasks-vision@0.10.22`がパッケージとして存在せずCDNがHTTP 404を返すことを一次原因として確認した。

