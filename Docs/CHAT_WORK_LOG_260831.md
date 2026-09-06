# Chat Work Log

## 2026-09-06

### 2026-09-06 22:04 JST - Codex GPT-5 - 種別: 依頼内容 - 裸眼立体感の機能改善

- 内容:

  ```text
  より裸眼で立体視可能な様に機能改善して。
  ```

### 2026-09-06 22:04 JST - Codex GPT-5 - 種別: 経過 - 実装方針と使用モデル

- 内容:

  Codex GPT-5系を継続使用し、動的切替なし。現在のHead-Coupled Perspectiveを維持しながら、単純に視差量を増やすのではなく、Depthに応じた視点投影、前景／背景の相対運動、接地影、被写体縁の視差補助を同じ顔／指ドラッグ視点へ同期する。設定可能な軽量処理として実装し、輪郭破綻、背景の引きずり、フレームレート、視差低減設定を回帰確認する。通常ディスプレイで左右眼へ別画像を送る真の裸眼ステレオではない制約は維持する。

### 2026-09-06 22:08 JST - Codex GPT-5 - 種別: 経過 - 修正前回帰

- 内容:

  裸眼3D強調の設定、ゼロ視差面を基準に手前と奥を逆方向へ分ける相対運動視差、顔サイズによる前後視点、視点連動の被写体背後影、画面端の空間ウィンドウ陰影、60／120Hzで追従速度を揃える経過時間ベース平滑化を要求する回帰検査を先に追加した。修正前の`index.html`に対して`裸眼3D強調切替のUIがありません`で意図どおりFAILすることを確認した。

### 2026-09-06 22:18 JST - Codex GPT-5 - 種別: 経過 - 実装・デスクトップ検証

- 内容:

  `index.html`へ裸眼3D強調ON/OFF、空間強調、画面面Depth、前後視点を追加した。shaderではゼロ視差面を基準にした相対運動、移動後マスクによる動的遮蔽、被写体背後影、画面端陰影を合成した。Face Landmarkerの両目間隔から前後移動を推定し、全視点値を経過時間ベースで平滑化した。人物自動分離の256pxマスクで階段状輪郭が見えたため、移動後マスクを9タップでソフト化した。

  ローカルHTTPのChromium WebGL 2.0で`Sample1.png`を読み込み、MediaPipe人物自動分離、Depth多層、横方向ドラッグ、前後視点0／1を確認した。表示は60fps、console errorなし。390x844ではbody幅390px、横スクロールなし、canvas 390x844、画像の縦横比維持、設定パネル幅370px・高さ約412px・内部スクロールを確認した。これはデスクトップブラウザのiPhone相当viewportであり、iPhone Safari実機確認ではない。

### 2026-09-06 22:22 JST - Codex GPT-5 - 種別: 結果 - commit／push／Pages確認

- 内容:

  実装と回帰検査を`d231ded`（`feat: strengthen naked-eye depth cues`）、設計書・README・変更履歴を`a62ff8b`（`docs: document head-coupled depth enhancement`）として`main`へpushした。品質ゲートrun `34035828416`、Pages run `34035828171`はいずれもsuccess。公開`index.html`とローカル`index.html`のSHA-256は`5f1f896174ffaad64dbde5cfb3f61573c3af76e1027f73f7c6d31dd190dac85a`で一致した。

  公開版`https://yoshikawa303.github.io/P-3D/?build=a62ff8b`を390x844で再確認し、`Sample1.png`読込、端末内人物分離、Depth多層3D、裸眼3D強調、前後視点1、60fps、横スクロールなし、console errorなしを確認した。iPhone Safari実機のカメラ権限、顔X／Y／Z追跡、実効フレームレート、見え方は未確認。使用モデルはCodex GPT-5系のまま、動的切替なし。
