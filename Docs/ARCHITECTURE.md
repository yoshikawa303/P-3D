# P-3D Architecture

## 1. 現在の構成

P-3DはGitHub Pagesで配信する静的Webアプリである。

```text
ユーザー画像 ─┬─ 任意Depth Map（白=手前）
              ├─ 任意人物／物体マスク（白=対象）
              └─ MediaPipe人物6カテゴリ分離（任意実行）
  ↓
WebGL image / depth / subject-mask textures
  ↓
フロントカメラ → MediaPipe Face Landmarker → 鼻位置
  ↓
viewX / viewY → WebGL parallax
```

顔追跡が使用できない場合は、ポインタ／タッチドラッグで `viewX` と `viewY` を更新する。

設定パネルは初期状態で非表示とし、画面右上のボタンで表示／非表示を切り替える。表示状態は`localStorage`の`p3d.settingsPanelVisible.v1`へ保存し、閉じた状態では`visibility: hidden`と`pointer-events: none`で操作対象から外す。Escキーでも閉じられる。

画像は、画像比率とcanvas比率からWebGLのUVを`contain`方式で補正する。横長画面ではX軸、縦長画面ではY軸のUV範囲を狭め、画像全体の縦横比を維持する。画像と画面の比率が異なる部分は黒い余白として表示し、画像を切り取らない。

### 表現モード

- `標準`: 中心位置と範囲から作るガウス分布Depthで、従来どおり滑らかな視差を付ける。
- `ホログラム`: Depth勾配から疑似法線を作り、`viewX / viewY`と疑似光源に追従するFresnel反射、鏡面ハイライト、分光色、色収差視差をfragment shaderで合成する。Depth Map／人物物体マスクがある場合は面方向と対象範囲の精度が上がる。
- `簡易ポップ3D`: 中心Depthをカード状へ強め、視差量、輪郭傾斜の明暗、中央ハイライトを加える。追加のDepth Mapを使わない軽量版であり、隠れた背景の復元や被写体輪郭の正確な立体化は行わない。
- `振動3D（背景固定）`: 背景は元UVで固定し、中心Depthを閾値で明確に切った前景近似マスクとして前景だけを微小移動する。画像輝度の4方向差分からDepth境界付近の強い輪郭候補を求め、白く合成して前後分離を強める。
- `Depth多層3D`: Depth値を近景／中景／遠景へ連続的に分け、追従速度の異なる3つの視点値で視差を付ける。人物／物体マスクは前景と背景の境界に使用する。Depth Mapが背景階調を持つ場合は遠景用の遅い視差、寒色の遠方減衰、Depth陰影も背景へ適用する。

全モードは同じ画像テクスチャ、顔追跡、指ドラッグを共有する。効果強度は材質反射または浮き彫り効果へ適用し、既存の立体強度は視差移動量として独立させる。

疑似照明は設定した光源X／YとDepth疑似法線の内積から、光源側の鏡面ハイライトと制御された白飛び、反対側の陰影を求める。Depth境界は輪郭光として追加し、`光・陰影強度`で一括調整する。これは元画像から光源を推定する処理ではなく、ユーザーが指定する演出用の疑似光源である。

### Depth Map・人物／物体マスク

- Depth Mapはグレースケール画像を端末内で読み込み、黒を遠方、白を手前として扱う。
- 人物／物体マスクは黒を背景、白を対象として扱う。newMosaic、画像編集ソフト、任意のセグメンテーション処理が生成したPNGを共通入力にできる。
- `人物を自動分離`は、選択済み画像をMediaPipe Image Segmenterへ渡し、背景、髪、身体の肌、顔の肌、服、その他の6カテゴリから人物マスクと部位Depthを端末内で生成する。結果画像はサーバーへ送信しない。
- newMosaicの`VNGeneratePersonInstanceMaskRequest`、Vision骨格、macOS用ONNX RuntimeをGitHub Pagesから直接実行することはできない。P-3Dとはマスク／Depth画像を境界として連携し、Safari側の自動人物分離にはWeb対応MediaPipeモデルを使う。
- 任意マスクは人物以外の物体にも使用できる。自動分離は人物用モデルであり、一般物体を自動認識するものではない。

振動3Dは`requestAnimationFrame`ごとに時刻をshaderへ渡すため、60Hz／120Hzなど端末とブラウザの実効描画更新へ追従する。120fpsをコード側で固定保証はしない。自動振動は約8Hz、テクスチャUVの最大振幅は横0.35%、縦0.16%とし、`prefers-reduced-motion`が有効な場合は振動成分だけを0にする。顔／指による前景視差は維持する。

## 2. カメラ・顔追跡の開始順

```text
ボタンのユーザー操作
  ↓
Secure Context / mediaDevices確認
  ↓
getUserMedia(facingMode: user)
  ↓
video.play()
  ↓
MediaPipe JavaScript module + WASM + model読込
  ↓
GPUでFaceLandmarker生成
  ├─ 成功 → VIDEO検出
  └─ 失敗 → CPUで再生成
```

カメラ要求を外部モジュール読込より先に置く。これにより、CDNやWASMが失敗してもカメラ権限処理へ到達し、原因を分離して表示できる。

## 3. 外部依存

|用途|固定参照|
|---|---|
|MediaPipe module|`@mediapipe/tasks-vision@1.0.1/vision_bundle.mjs`|
|MediaPipe WASM|`@mediapipe/tasks-vision@1.0.1/wasm`|
|Face Landmarker model|Google Storageの`face_landmarker/float16/1`|
|Image Segmenter model|Google Storageの`selfie_multiclass_256x256/float32/1`|

依存を更新する場合は、配布URLがHTTP 200であること、API互換性、iPhone Safari実機を確認する。

## 4. 状態の分離

- `cameraOn`: カメラstreamとvideo再生が開始済み。
- `trackingOn`: Face Landmarkerが初期化済みでフレーム検出可能。
- `startingFace`: 起動処理の多重実行を防止。
- `hasDepthMap` / `hasSubjectMask`: 任意または人物自動分離で生成した補助テクスチャの有無。
- `nearView` / `midView` / `farView`: 同じ顔／ドラッグ視点へ異なる追従係数を適用した多層視差状態。
- カメラ失敗: 手動モードへ戻してカメラ再試行を提示。
- 顔検出準備失敗: カメラを停止せず、手動操作と顔追跡再試行を提示。

## 5. 将来構成

5モードと任意Depth／マスクを基準に、一般物体のWeb自動セグメンテーション、newMosaicのDepth／マスク書出し、背景Inpainting、Disocclusion補正、Off-Axis Projectionへ段階的に拡張する。各段階でiPhone Safari実機の性能とプライバシーを再評価する。
