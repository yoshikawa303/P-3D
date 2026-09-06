# Chat Work Log

## 2026-09-07

### 2026-09-07 00:38 JST - Codex GPT-5 - 種別: 依頼内容 - コスト効率を優先した立体視改善

- 内容:

  ```text
  ★コスパ良く実装して
  ```

### 2026-09-07 00:38 JST - Codex GPT-5 - 種別: 経過 - 実装方針と使用モデル

- 内容:

  Codex GPT-5系を継続使用し、動的切替なし。既存の人物／物体マスク、Depth Map、顔／ドラッグ視点追従、WebGL shaderを再利用し、新しいAIモデルや外部アップロードを追加せずに、だまし絵の額縁越境、背景の透視変形、額縁の疑似厚み、背後影を組み合わせる「トリックポータル3D」を実装する。単独モードと複合エフェクトの個別強度に対応し、自動回帰、デスクトップ表示、モバイル相当viewport、Public GitHub Pagesを検証する。iPhone Safari実機確認とは区別して記録する。

### 2026-09-07 00:40 JST - Codex GPT-5 - 種別: 経過 - 修正前回帰

- 内容:

  6番目の立体表現モード、単独／複合処理の個別強度、背景透視変形、ポータル内側と額縁の判定、被写体を額縁より手前へ合成する順序、ポータル強度に応じた背後影を要求する回帰検査を先に追加した。修正前の`index.html`に対して`立体表現モードがありません: トリックポータル3D`で意図どおりFAILすることを確認した。

### 2026-09-07 00:45 JST - Codex GPT-5 - 種別: 経過 - 実装・ローカル検証

- 内容:

  `index.html`へ6番目の`トリックポータル3D`と、複合エフェクト用ON/OFF・専用強度を追加した。fragment shaderでは背景だけを台形透視と視点連動で変形し、暗く抑えた外壁、疑似光源に追従する額縁、人物／物体前景の順で合成して額縁越境を作った。既存の接地影はポータル強度でも有効にし、新しいAIモデルや外部アップロードは追加していない。

  ローカルHTTPのChromium WebGL 2.0で`Sample1.png`を読み込み、単独トリックポータル、MediaPipe人物自動分離、Depth多層＋トリックポータルの複合、専用強度0.84、設定初期化を確認した。60fps、JavaScript／WebGL errorなし。MediaPipeのOpenGL error checking無効化の情報warnのみ。390x844ではbody幅390px、横スクロールなし、canvas 390x844、画像縦横比0.7462039が入力比率と一致、設定パネル幅370px・高さ約412px・内部スクロール、全画面表示を確認した。これはデスクトップブラウザのiPhone相当viewportであり、iPhone Safari実機確認ではない。

  バンドル済みNode.jsをPATHへ追加して`python3 scripts/ci/web_regression_gate.py`を実行し、JavaScript構文を含む全検査がPASSした。

### 2026-09-07 00:49 JST - Codex GPT-5 - 種別: 結果 - commit／push／Pages確認

- 内容:

  実装と回帰検査を`5c3e734`（`feat: add lightweight trick portal 3d`）、設計書・README・変更履歴・週次ログを`08c4484`（`docs: document trick portal workflow`）として既存`main`へpushした。品質ゲートrun `34043407766`、Pages run `34043407127`はいずれもsuccess。ローカル`index.html`と公開`index.html`のSHA-256は`9b6f093261c61b6366a0c7412e5db21f88b5f81dcd470aad23ce6c1de960bf55`で一致した。

  公開版`https://yoshikawa303.github.io/P-3D/?build=08c4484`を390x844で開き、6番目のトリックポータル3D、Depth多層＋トリックポータル複合、専用強度0.84、横スクロールなし、console errorなしを確認した。ローカル作業場所はGit checkoutではないため`git init`せず、一時checkoutと一時indexを使用した。Codex GPT-5系を継続使用し、動的切替なし。iPhone Safari実機のカメラ／顔追跡、タッチ操作、実効fps、発熱、電力、立体感の官能評価は未確認。
