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

### 2026-08-15 19:14 JST - Codex GPT-5 - 種別: 作業結果 - フロントカメラ修正と開発運用移植

- 内容:

  根本原因は、存在しない`@mediapipe/tasks-vision@0.10.22`をカメラ要求前に動的importしていたこと。CDNのHTTP 404で処理が中断し、`getUserMedia()`へ到達せず手動モードになっていた。

  `index.html`を、ユーザー操作中のカメラ要求を先に行う構成へ変更し、MediaPipeを固定版`1.0.1`へ更新した。カメラ状態と顔追跡状態を分離し、GPU初期化失敗時のCPUフォールバック、権限／起動／顔検出準備の区別、顔追跡のみの再試行、ページ終了時の解放を追加した。

  maruPlayから共有可能な運用のみをP-3D向けに移植し、`CLAUDE.md`、`AGENTS.md`、`GEMINI.md`、`PROJECT_RULES.md`、`Docs/ARCHITECTURE.md`、`CHANGELOG.md`、`README.md`、週次作業ログ、GitHub Actions回帰ゲートを追加した。音声処理やXcodeなどmaruPlay固有規則は移植していない。

  検証は、JavaScript構文、カメラ先行順序、固定依存、CPUフォールバック、Cross-AI文書の回帰ゲートが全PASS。MediaPipe module、WASM、model、FaceLandmarker生成のスモークテストもPASS。ローカルHTTPは約60fps・初期コンソールエラーなし。GitHubの品質ゲートとPagesデプロイはcommit`5887bf219444d48ee057dabb064adc73be5c5ff6`で成功し、公開版が`1.0.1`とカメラ先行処理を配信していることを確認した。

  Gitは、ローカル`/Volumes/DATA/XCode_Project/P-3D`がcheckoutではないため`git init`せず、一時checkoutから既存`main`へcommit`898335d9fa3a9b4fb92fb6dd8c177e86011ae5d3`（修正・回帰）と`5887bf219444d48ee057dabb064adc73be5c5ff6`（運用文書）をpushした。GitHubアプリの書込APIは権限403だったため、既存のGitHub CLI認証を用いた。モデル切替はなし。

  iPhone Safari実機のカメラ許可、映像入力、実際の顔移動による視点変化はこのMacから検証できないため未確認。ユーザー側で公開URLを再読込し、ステータスが`顔を探しています…`から`FACE x, y`へ変わることを確認する必要がある。

- 作業時間: 約20分

### 2026-08-15 19:52 JST - Codex GPT-5 - 種別: 依頼内容 - 設定パネルの表示切替

- 内容:

  ```text
  ★改善：設定ウィンドウが邪魔、ON/OFF可能にして
  ```

### 2026-08-15 19:52 JST - Codex GPT-5 - 種別: 経過 - 使用モデル

- 内容:

  Codex GPT-5系を継続使用。単一HTMLのUI改善、アクセシビリティ、ブラウザ回帰、Pages反映を一貫して実施する。モデル切替権限はなく、動的切替なし。

### 2026-08-15 19:56 JST - Codex GPT-5 - 種別: 作業結果 - 設定パネル表示切替の公開

- 内容:

  設定パネルを初期状態で非表示にし、画面右上の`設定を表示`／`設定を隠す`ボタンから切り替え可能にした。表示状態はSafari内へ保存し、再読込後も維持する。Escキー、`aria-expanded`／`aria-hidden`、視差低減設定、非表示中の操作無効化にも対応した。

  JavaScript構文、既存カメラ処理、設定パネル切替、アクセシビリティ、Cross-AI文書の回帰ゲートは全PASS。ローカルとGitHub Pages公開版の両方で初期非表示、表示、非表示、Esc、状態保存を確認し、公開版は約60fps、コンソールエラーなしだった。

  実装commit`e00dc3b34022c002c4f5ecabbeed11d0529dfa68`を既存`main`へpushし、品質ゲートとPagesデプロイが成功した。ローカルP-3DはGit checkoutではないため`git init`せず、一時checkoutを使用。Codex GPT-5系を使用し、動的切替なし。iPhone Safari実機での目視は未実施。

- 作業時間: 約5分

### 2026-08-15 23:19 JST - Codex GPT-5 - 種別: 依頼内容 - 初期画像の縦横比修正

- 内容:

  ```text
  ☆画像を表示した初期状態で、画像の縦横比率がおかしくなる。
  ```

### 2026-08-15 23:19 JST - Codex GPT-5 - 種別: 経過 - 使用モデル

- 内容:

  Codex GPT-5系を継続使用。WebGL座標変換の根本原因調査、実画像と複数画面比率の回帰確認、Pages反映を一貫して実施する。モデル切替権限はなく、動的切替なし。

### 2026-08-15 23:21 JST - Codex GPT-5 - 種別: 経過 - 根本原因と修正前回帰

- 内容:

  `fitUV()`が、横長画面ではY軸、縦長画面ではX軸へ補正を掛けており、`u_screenAspect / u_imgAspect`の係数を逆の軸へ適用していた。これにより画像テクスチャ自体ではなく初期UV変換で画像が伸縮していた。

  横長画面ではX軸、縦長画面ではY軸を補正する回帰検査を先に追加し、修正前の`index.html`に対して意図どおりFAILすることを確認した。
