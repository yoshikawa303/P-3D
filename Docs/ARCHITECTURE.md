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

MVPの中心領域による疑似Depthから、人物セグメンテーション、Depth Map、背景Inpainting、Disocclusion補正、Off-Axis Projectionへ段階的に拡張する。各段階でiPhone Safari実機の性能とプライバシーを再評価する。
