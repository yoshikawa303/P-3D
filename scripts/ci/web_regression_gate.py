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


def displayed_aspect_after_contain_uv(screen_aspect: float, image_aspect: float) -> float:
    """Return the physical aspect produced by the shader's contain transform."""
    ratio = screen_aspect / image_aspect
    if ratio > 1.0:
        normalized_width, normalized_height = 1.0 / ratio, 1.0
    else:
        normalized_width, normalized_height = 1.0, ratio
    return screen_aspect * normalized_width / normalized_height


def main() -> int:
    html = INDEX.read_text(encoding="utf-8")

    require(
        "if(ratio>1.0) p.x*=ratio;" in html,
        "横長画面では画像UVのX軸を補正し、縦横比を保持してください",
    )
    require(
        "else p.y/=ratio;" in html,
        "縦長画面では画像UVのY軸を補正し、縦横比を保持してください",
    )
    for screen_aspect, image_aspect in [
        (2.0, 1.0),
        (0.5, 1.0),
        (16.0 / 9.0, 4.0 / 3.0),
        (9.0 / 19.5, 688.0 / 922.0),
    ]:
        actual_aspect = displayed_aspect_after_contain_uv(screen_aspect, image_aspect)
        require(
            abs(actual_aspect - image_aspect) < 1e-9,
            f"contain補正後の画像比率が不正です: {screen_aspect=} {image_aspect=} {actual_aspect=}",
        )

    require('id="effectMode"' in html, "立体表現モードの選択UIがありません")
    for value, label in [
        ("0", "標準"),
        ("1", "ホログラム"),
        ("2", "簡易ポップ3D"),
        ("3", "振動3D（背景固定）"),
        ("4", "Depth多層3D"),
    ]:
        require(
            f'<option value="{value}">{label}</option>' in html,
            f"立体表現モードがありません: {label}",
        )
    require('id="effectStrength"' in html, "効果強度の設定UIがありません")
    require("uniform float u_effectMode;" in html, "立体表現モードのshader uniformがありません")
    require("uniform float u_effectStrength;" in html, "効果強度のshader uniformがありません")
    require("vec3 hologramColor(float phase)" in html, "ホログラム色のshader処理がありません")
    for element_id, label in [
        ("combineEffects", "複合処理切替"),
        ("enableHologram", "ホログラム合成"),
        ("enableRelief", "ポップ3D合成"),
        ("enableVibration", "振動3D合成"),
        ("enableDepthLayers", "Depth多層3D合成"),
        ("hologramStrength", "ホログラム個別強度"),
        ("reliefStrength", "ポップ3D個別強度"),
        ("vibrationStrength", "前景微振動個別強度"),
        ("depthLayerStrength", "Depth多層個別強度"),
        ("edgeCleanup", "共通輪郭ぼかし"),
        ("hologramNearSuppression", "近景ホログラム抑制"),
    ]:
        require(f'id="{element_id}"' in html, f"{label}のUIがありません")
    require("function effectFlags()" in html, "単独モードと複合処理を統合する処理がありません")
    require("function effectStrengths()" in html, "複合処理ごとの独立強度を統合する処理がありません")
    for uniform in [
        "uniform float u_enableHologram;",
        "uniform float u_enableRelief;",
        "uniform float u_enableVibration;",
        "uniform float u_enableDepthLayers;",
        "uniform float u_hologramStrength;",
        "uniform float u_reliefStrength;",
        "uniform float u_vibrationStrength;",
        "uniform float u_depthLayerStrength;",
        "uniform float u_edgeCleanup;",
        "uniform float u_hologramNearSuppression;",
    ]:
        require(uniform in html, f"複合／輪郭処理のshader uniformがありません: {uniform}")
    require("float subjectBoundaryAt(vec2 uv)" in html, "人物／物体境界の検出処理がありません")
    require("vec3 softBlurAt(vec2 uv)" in html, "不要輪郭のソフトぼかし処理がありません")
    require("vec3 applyCommonCleanup" in html, "各モード共通の輪郭抑制処理がありません")
    require("applyCommonCleanup" in html[html.index("void main()") :], "最終描画へ共通輪郭抑制を適用していません")
    require("float hologramDepthAttenuation=" in html, "Depthに応じたホログラム強度制御がありません")
    require("u_hologramNearSuppression" in html, "近景ホログラム抑制値をshaderで利用していません")
    for use in [
        "float hologramStrength=clamp(u_hologramStrength",
        "float reliefStrength=clamp(u_reliefStrength",
        "float vibrationStrength=clamp(u_vibrationStrength",
        "float depthLayerStrength=clamp(u_depthLayerStrength",
    ]:
        require(use in html, f"個別強度をshaderで利用していません: {use}")
    for element_id, label in [
        ("depthFile", "Depth Map入力"),
        ("subjectMaskFile", "人物／物体マスク入力"),
        ("autoPerson", "端末内人物分離"),
        ("clearMaps", "マップ解除"),
        ("mapStatus", "マップ状態表示"),
        ("lightX", "疑似光源X"),
        ("lightY", "疑似光源Y"),
        ("lightingStrength", "光・陰影強度"),
    ]:
        require(f'id="{element_id}"' in html, f"{label}のUIがありません")
    for uniform in [
        "uniform sampler2D u_depthTex;",
        "uniform sampler2D u_subjectMaskTex;",
        "uniform float u_hasDepthMap;",
        "uniform float u_hasSubjectMask;",
        "uniform vec2 u_viewNear;",
        "uniform vec2 u_viewMid;",
        "uniform vec2 u_viewFar;",
        "uniform vec2 u_lightDirection;",
        "uniform float u_lightingStrength;",
    ]:
        require(uniform in html, f"Depth多層描画のshader uniformがありません: {uniform}")
    require("float sampledDepthAt(vec2 uv)" in html, "任意Depth Mapの参照処理がありません")
    require("float subjectMaskAt(vec2 uv)" in html, "人物／物体マスクの参照処理がありません")
    require("vec3 depthNormalAt(vec2 uv)" in html, "Depth勾配から疑似法線を求める処理がありません")
    require("float fresnel=" in html, "ホログラムの視点依存Fresnel反射がありません")
    require("vec3 chromaticSample=" in html, "ホログラムの色収差視差がありません")
    require("layeredView=mix(u_viewFar,u_viewMid" in html, "遠景／中景の視差遅延合成がありません")
    require("layeredView=mix(layeredView,u_viewNear" in html, "近景の視差遅延合成がありません")
    require("vec2 backgroundOffset=u_viewFar*u_depth*d" in html, "背景Depthの遠景視差がありません")
    require("float whiteHighlight=" in html, "人物／物体の入射光による白飛びがありません")
    require("float surfaceShadow=" in html, "光源と反対側の陰影がありません")
    require("float aerialDepth=" in html, "背景空間の遠方減衰がありません")
    require("selfie_multiclass_256x256/float32/1" in html, "固定版の人物部位分離モデルがありません")
    require("ImageSegmenter.createFromOptions" in html, "端末内人物分離の初期化がありません")
    require("function depthForPersonPart(category)" in html, "人物部位別Depth割当がありません")
    require("result.categoryMask.getAsUint8Array()" in html, "人物カテゴリマスクをテクスチャ化していません")
    require("uniform float u_time;" in html, "フレーム同期時刻のshader uniformがありません")
    require("uniform vec2 u_texelSize;" in html, "輪郭検出用texelサイズのshader uniformがありません")
    require("uniform float u_motionScale;" in html, "視差低減用のshader uniformがありません")
    require("float imageEdgeAt(vec2 uv)" in html, "画像輪郭の検出処理がありません")
    require(
        "backgroundUV=base;" in html,
        "振動3Dで背景を固定サンプリングしていません",
    )
    require(
        "float proceduralMask=smoothstep(0.42,0.72,proceduralDepthAt(uv));" in html,
        "Depth Map未使用時も前景マスクの裾が背景領域へ残らないようにしてください",
    )
    require(
        "const reduceMotion=window.matchMedia(\"(prefers-reduced-motion: reduce)\")" in html,
        "振動3Dが視差低減設定を参照していません",
    )
    require(
        "gl.uniform1f(U.u_motionScale,reduceMotion.matches ? 0 : 1)" in html,
        "視差低減設定をshaderへ渡していません",
    )
    require("requestAnimationFrame(render)" in html, "表示更新が画面リフレッシュへ追従していません")
    require(
        'gl.uniform1f(U.u_effectMode,parseFloat($("#effectMode").value))' in html,
        "立体表現モードをshaderへ渡していません",
    )
    require(
        'gl.uniform1f(U.u_effectStrength,parseFloat($("#effectStrength").value))' in html,
        "効果強度をshaderへ渡していません",
    )

    require('id="guide"' in html, "編集対象を示すガイドcanvasがありません")
    require("function drawGuides()" in html, "中心・範囲・光源・認識領域の動的ガイドがありません")
    require("function updateRecognitionGuide(source)" in html, "認識マスクから編集ガイドを作成していません")
    require("function guideDragTargetAt(event)" in html, "画像上の編集ハンドル判定がありません")
    require("function updateGuideDrag(event)" in html, "画像上のガイドドラッグ編集がありません")
    require('stage.addEventListener("pointerdown",beginGuideDrag,true)' in html, "ガイドの直接ドラッグ開始処理がありません")
    for element_id, label in [
        ("contourCrop", "人物／物体輪郭トリミング"),
        ("cropFeather", "トリミング輪郭ぼかし"),
        ("undoEdit", "アンドゥ"),
        ("redoEdit", "リドゥ"),
        ("resetDefaults", "初期値へ戻す"),
    ]:
        require(f'id="{element_id}"' in html, f"{label}のUIがありません")
    for removed in ['id="cropLeft"', 'id="cropRight"', 'id="cropTop"', 'id="cropBottom"', "uniform vec4 u_cropRect;"]:
        require(removed not in html, f"矩形トリミングが残っています: {removed}")
    require("uniform float u_contourCrop;" in html, "輪郭トリミングのshader uniformがありません")
    require("uniform float u_cropFeather;" in html, "トリミング輪郭ぼかしのshader uniformがありません")
    require("float contourCropMaskAt(vec2 uv)" in html, "人物／物体輪郭トリミングのshader処理がありません")
    require("texture2D(u_subjectMaskTex" in html[html.index("float contourCropMaskAt") :], "入力マスク輪郭をトリミングへ利用していません")
    require("c.rgb*=contourCropMaskAt(foregroundUV);" in html, "最終描画を人物／物体輪郭で切り抜いていません")
    require("function syncContourCropAvailability()" in html, "マスク有無に応じた輪郭トリミング制御がありません")
    require(
        "function filterSubjectComponents(categories,width,height)" in html,
        "人物自動分離の微小な孤立誤検知を除去する処理がありません",
    )
    require(
        "function isPersonCategory(category)" in html,
        "人物自動分離で非人物カテゴリを除外する判定がありません",
    )
    require(
        "const filteredSubject=filterSubjectComponents(categories,width,height);" in html,
        "連結領域フィルタが人物マスク生成に適用されていません",
    )
    require("const core=new Uint8Array(total);" in html, "細い誤接続を分離するマスク収縮がありません")
    require(
        "labels[nextY*width+nextX]===largestLabel" in html,
        "主被写体以外の孤立領域が人物マスクへ残ります",
    )
    require("function captureEditState()" in html, "編集状態の取得処理がありません")
    require("function applyEditState(state)" in html, "編集状態の復元処理がありません")
    require("function pushEditHistory()" in html, "アンドゥ／リドゥ履歴処理がありません")
    for removed in ['id="sample1"', 'id="sample2"', '$("#sample1")', '$("#sample2")']:
        require(removed not in html, f"削除対象のサンプルUI／処理が残っています: {removed}")

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

    print("PASS: image aspect ratio preservation across portrait and landscape screens")
    print("PASS: five effect modes including Depth Map layered 3D")
    print("PASS: stackable effects, common contour cleanup, and near-depth hologram control")
    print("PASS: draggable guides, mask-contour crop, undo/redo, and reset defaults")
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
