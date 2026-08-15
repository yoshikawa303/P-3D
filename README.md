# P-3D

iPhoneのフロントカメラで閲覧者の顔位置を追跡し、2DポスターをWebGLで擬似立体表示する技術検証です。

- 公開版: <https://yoshikawa303.github.io/P-3D/>
- 画像とカメラフレームはブラウザ内で処理します。
- `Depth多層3D`では、白が手前のDepth Mapと、白が対象の人物／物体マスクを任意入力できます。
- 選択画像に対する人物自動分離も端末内で実行し、画像を外部サーバーへアップロードしません。
- 正式な顔追跡確認には、HTTPSの公開版をiPhone Safariで開いてカメラを許可してください。

## 開発確認

```bash
python3 scripts/ci/web_regression_gate.py
python3 -m http.server 8080
```

`http://localhost:8080/` はデスクトップ確認用です。iPhoneからMacのLAN内HTTPへアクセスする方式ではSecure Contextにならず、カメラを利用できない場合があります。

AIごとの入口は `CLAUDE.md`、`AGENTS.md`、`GEMINI.md` を参照してください。
