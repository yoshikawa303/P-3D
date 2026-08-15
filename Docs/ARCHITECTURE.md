# P-3D Architecture

## 1. 現在の構成

P-3DはGitHub Pagesで配信する静的Webアプリである。

```text
ユーザー画像
  ↓
WebGL texture + 疑似Depth
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
- `ホログラム`: `viewX / viewY`に追従する分光色、反射帯、ハイライトをfragment shaderで合成する。追加画像や外部通信は使用しない。
- `簡易ポップ3D`: 中心Depthをカード状へ強め、視差量、輪郭傾斜の明暗、中央ハイライトを加える。追加のDepth Mapを使わない軽量版であり、隠れた背景の復元や被写体輪郭の正確な立体化は行わない。
- `振動3D（背景固定）`: 背景は元UVで固定し、中心Depthを閾値で明確に切った前景近似マスクとして前景だけを微小移動する。画像輝度の4方向差分からDepth境界付近の強い輪郭候補を求め、白く合成して前後分離を強める。

全モードは同じ画像テクスチャ、顔追跡、指ドラッグを共有する。効果強度は材質反射または浮き彫り効果へ適用し、既存の立体強度は視差移動量として独立させる。

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

依存を更新する場合は、配布URLがHTTP 200であること、API互換性、iPhone Safari実機を確認する。

## 4. 状態の分離

- `cameraOn`: カメラstreamとvideo再生が開始済み。
- `trackingOn`: Face Landmarkerが初期化済みでフレーム検出可能。
- `startingFace`: 起動処理の多重実行を防止。
- カメラ失敗: 手動モードへ戻してカメラ再試行を提示。
- 顔検出準備失敗: カメラを停止せず、手動操作と顔追跡再試行を提示。

## 5. 将来構成

軽量な4モードを基準に、人物セグメンテーション、任意Depth Map、背景Inpainting、Disocclusion補正、Off-Axis Projectionへ段階的に拡張する。各段階でiPhone Safari実機の性能とプライバシーを再評価する。
