# P-3D Project Rules

## 目的

1枚の2Dポスター画像をWebGLで擬似立体化し、iPhoneのフロントカメラで取得した閲覧者の顔位置に応じて視点を変化させる。通常ディスプレイで左右眼へ別画像を送る裸眼ステレオではなく、1人向けのHead-Coupled Perspectiveを提供する。

## 恒久的な技術制約

- MVPはGitHub Pages上の静的HTML／JavaScriptとして動作し、HTTPSを必須とする。
- カメラ処理は `getUserMedia()` → `<video playsinline muted>` → 顔検出初期化の順にする。
- カメラが起動でき、顔検出だけ失敗した場合は、カメラとエラー状態を保持して顔追跡再試行を可能にする。
- 顔検出が使えない場合も画像表示と指ドラッグ操作を維持する。
- MediaPipe Tasks Visionは検証済み固定版を使い、GPU初期化失敗時はCPUへフォールバックする。
- 選択画像と映像フレームは端末内処理とし、ネットワーク送信機能を追加する場合は事前に仕様とプライバシー影響の承認を得る。
- 正しい顔連動の合格判定はiPhone Safari実機1人分で行う。デスクトップやシミュレーションだけでは正式PASSにしない。

## 変更時の確認対象

- カメラ／顔追跡: HTTPS、権限、前面カメラ、動画再生、MediaPipe module、WASM、model、GPU／CPU、顔ランドマーク。
- 描画: WebGL生成、テクスチャ、画像アスペクト比、フレームレート、手動ドラッグ。
- 公開: case-sensitiveなファイル名、相対URL、`main` のcommit SHA、Pages反映。
- 画像: Publicリポジトリへ著作権画像・個人画像を追加しない。

## 仕様変更の事前確認

次はバグ修正として独断で変更しない。

- カメラ映像・選択画像のアップロードや保存
- 外部解析APIへの送信
- ユーザー向け画像選択、手動操作、カメラ操作の削除または自動化
- Head-Coupled Perspectiveから別方式への変更
- Public／Privateやホスティング方式の変更

