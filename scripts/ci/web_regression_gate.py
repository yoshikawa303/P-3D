#!/usr/bin/env python3
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / "index.html"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    html = INDEX.read_text(encoding="utf-8")

    require("@mediapipe/tasks-vision@0.10.22" not in html, "存在しないMediaPipe 0.10.22参照が残っています")
    require(
        "@mediapipe/tasks-vision@1.0.1/vision_bundle.mjs" in html,
        "検証済みMediaPipe moduleの固定URLがありません",
    )
    require("@mediapipe/tasks-vision@1.0.1/wasm" in html, "MediaPipe WASMの固定URLがありません")
    require("window.isSecureContext" in html, "Secure Context検査がありません")
    require("navigator.mediaDevices.getUserMedia" in html, "getUserMedia呼び出しがありません")
    require('facingMode:{ideal:"user"}' in html, "フロントカメラ指定がありません")
    require('delegate:"GPU"' in html, "GPU初期化がありません")
    require("retrying with CPU" in html, "GPU失敗時のCPUフォールバックがありません")

    start_match = re.search(
        r"async function startFace\(\)\{(?P<body>.*?)\n\}\n\$\(\"#camera\"\)",
        html,
        re.DOTALL,
    )
    require(start_match is not None, "startFace関数を取得できません")
    start_body = start_match.group("body")
    require(
        start_body.index("await startCamera()") < start_body.index("await createFaceLandmarker()"),
        "カメラ要求は顔検出モジュール初期化より先に実行してください",
    )
    require("カメラは起動しましたが、顔検出の準備に失敗しました" in start_body, "失敗境界の表示がありません")
    require("顔追跡を再試行" in start_body, "顔追跡だけを再試行する導線がありません")

    require('id="panelToggle"' in html, "設定パネルの切替ボタンがありません")
    require('aria-controls="panel"' in html, "設定パネル切替のaria-controlsがありません")
    require('aria-expanded="false"' in html, "設定パネル切替の初期aria-expandedが不正です")
    require('id="panel" class="is-hidden" aria-hidden="true"' in html, "設定パネルが初期非表示ではありません")
    require('panel.classList.toggle("is-hidden",!visible)' in html, "設定パネルの表示切替処理がありません")
    require('panel.setAttribute("aria-hidden",String(!visible))' in html, "設定パネルのaria-hidden更新がありません")
    require('panelToggle.setAttribute("aria-expanded",String(visible))' in html, "切替ボタンのaria-expanded更新がありません")
    require("p3d.settingsPanelVisible.v1" in html, "設定パネルの表示状態保存がありません")
    require("prefers-reduced-motion:reduce" in html, "視差低減設定への対応がありません")

    for required in [
        "CLAUDE.md",
        "AGENTS.md",
        "GEMINI.md",
        "PROJECT_RULES.md",
        "Docs/ARCHITECTURE.md",
        "CHANGELOG.md",
    ]:
        require((ROOT / required).is_file(), f"必須文書がありません: {required}")

    node = shutil.which("node")
    if node:
        inline_scripts = re.findall(r"<script(?:\s[^>]*)?>(.*?)</script>", html, re.DOTALL)
        require(bool(inline_scripts), "インラインJavaScriptがありません")
        with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8") as script:
            script.write("\n".join(inline_scripts))
            script.flush()
            subprocess.run([node, "--check", script.name], check=True)
        print("PASS: JavaScript syntax")
    else:
        print("SKIP: nodeがないためJavaScript構文検査を省略")

    print("PASS: camera-before-MediaPipe ordering")
    print("PASS: pinned MediaPipe dependency and CPU fallback")
    print("PASS: settings panel visibility toggle and accessibility")
    print("PASS: Cross-AI governance documents")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, ValueError, subprocess.CalledProcessError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        raise SystemExit(1)
