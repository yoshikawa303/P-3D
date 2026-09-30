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
    for demo_path in [
        "assets/demos/demo-mascot.jpg",
        "assets/demos/demo-mascot-background.jpg",
        "assets/demos/demo-mascot-foreground.png",
        "assets/demos/demo-heroine.jpg",
        "assets/demos/demo-heroine-background.jpg",
        "assets/demos/demo-heroine-foreground.png",
        "assets/demos/demo-fluffy.jpg",
        "assets/demos/demo-fluffy-background.jpg",
        "assets/demos/demo-fluffy-foreground.png",
        "assets/demos/standee-stage.jpg",
        "assets/demos/demo-standee-girl-celestial.png",
        "assets/demos/demo-standee-girl-celestial-thumb.png",
        "assets/demos/demo-standee-girl-cyber.png",
        "assets/demos/demo-standee-girl-cyber-thumb.png",
        "assets/demos/demo-standee-man-royal.png",
        "assets/demos/demo-standee-man-royal-thumb.png",
        "assets/demos/demo-standee-man-street.png",
        "assets/demos/demo-standee-man-street-thumb.png",
        "assets/demos/demo-mascot-standee-thumb.png",
        "assets/demos/demo-fluffy-standee-thumb.png",
    ]:
        require((ROOT / demo_path).is_file(), f"デモ画像がありません: {demo_path}")
        require(demo_path in html, f"デモ画像がUIから参照されていません: {demo_path}")
    for element_id, label in [
        ("demoNext", "デモ画像切替ボタン"),
        ("demoGallery", "デモ画像ギャラリー"),
    ]:
        require(f'id="{element_id}"' in html, f"{label}がありません")
    require("const DEMO_ASSETS=[" in html, "デモ画像のプリセット定義がありません")
    require("function loadDemo(index" in html, "デモ画像を読み込む処理がありません")
    require("uniform sampler2D u_backgroundTex;" in html, "デモ背景の独立テクスチャがありません")
    require("uniform sampler2D u_foregroundTex;" in html, "透過立ち絵の独立テクスチャがありません")
    require("uniform float u_hasLayeredDemo;" in html, "2層デモの切替uniformがありません")
    require("vec4 sourceColorAt(vec2 uv)" in html, "背景と透過立ち絵の合成処理がありません")
    require(html.count("data-demo-index=") >= 9, "背景なしゆるキャラ／モフモフを含む9種類以上のデモがありません")
    require("ゆるアクスタ（透過）" in html, "背景なしゆるキャラのアクスタデモがありません")
    require("モフモフアクスタ（透過）" in html, "背景なしモフモフ動物のアクスタデモがありません")
    for element_id, label in [
        ("autoMotion", "アクスタ自動モーション切替"),
        ("motionStrength", "簡易重力モーション強度"),
    ]:
        require(f'id="{element_id}"' in html, f"{label}のUIがありません")
    for uniform in [
        "uniform float u_autoRigEnabled;",
        "uniform vec2 u_bodyMotion;",
        "uniform vec2 u_headMotion;",
        "uniform vec2 u_materialMotion;",
        "uniform vec2 u_propMotion;",
        "uniform vec4 u_rigCenters;",
        "uniform vec4 u_rigRadii;",
        "uniform vec4 u_materialRegion;",
        "uniform float u_standeeMode;",
    ]:
        require(uniform in html, f"アクスタ疑似リグのshader uniformがありません: {uniform}")
    require("function stepRigSpring(" in html, "簡易重力ばねの更新処理がありません")
    require("const rigSprings=" in html, "部位別の独立ばね状態がありません")
    require("stepRigSpring(rigSprings.body" in html, "胴体の独立ばねがありません")
    require("stepRigSpring(rigSprings.head" in html, "頭部の独立ばねがありません")
    require("stepRigSpring(rigSprings.material" in html, "髪／布の独立ばねがありません")
    require("stepRigSpring(rigSprings.prop" in html, "小物の独立ばねがありません")
    require("vec2 riggedForegroundUV(vec2 uv)" in html, "部位別の微小UV変形がありません")
    require("float acrylicSweep=" in html, "アクスタ内側の透明素材表現がありません")
    require("acrylicRim" not in html, "アクスタへ常時着色する輪郭反射が残っています")
    require(
        "abs((base.x+base.y*0.24)-(0.16+mod(u_time*0.075,1.28)))/0.13" in html,
        "アクスタ反射帯を0〜1へ収める幅正規化がありません",
    )
    require("function alphaBounds(source)" in html, "透過輪郭の自動認識がありません")
    require("function prepareStandeeForStage(source,demo)" in html, "展示背景へアクスタを自動配置できません")
    require("targetBottom=demo.stageBottom||0.84" in html, "アクスタの足元が展示台へ揃いません")
    require("activeRigProfile=prepared?.rig||demo.rig||null" in html, "認識結果を自動リグへ使用していません")
    require("uniform vec4 u_live2dMotion;" in html, "瞬き・口元・呼吸のLive2D風uniformがありません")
    require("float eyeBand=" in html and "float mouthBand=" in html, "顔領域の自動モーションがありません")
    require("const blinkPulse=" in html and "const breathMotion=" in html, "自動瞬き・呼吸がありません")
    require("float cleanLayerAlphaAt(vec2 uv)" in html, "透過立ち絵の低alpha色かぶりを除く境界処理がありません")
    require("float displacedForegroundMask=softSubjectMaskAt(foregroundUV);" in html, "移動後マスクを最終合成へ使用していません")
    require("foregroundMask=displacedForegroundMask;" in html, "移動前マスクが最終合成へ残る可能性があります")
    require("vec2 shadowUV=mix(base,foregroundUV,u_hasLayeredDemo);" in html, "背後影が移動前輪郭へ残ります")
    require("float groundBand=1.0-smoothstep" in html, "背後影が足元以外の全輪郭へ回り込みます")
    require("loadDemo(0,{hidePanel:false,recordHistory:false});" in html, "初回表示でデモ画像を鑑賞できません")
    require('aria-pressed="false"' in html, "デモ選択状態のアクセシビリティ属性がありません")
    for value, label in [
        ("0", "標準"),
        ("1", "ホログラム"),
        ("2", "簡易ポップ3D"),
        ("3", "振動3D（背景固定）"),
        ("4", "Depth多層3D"),
        ("5", "トリックポータル3D"),
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
        ("enableTrickPortal", "トリックポータル3D合成"),
        ("hologramStrength", "ホログラム個別強度"),
        ("reliefStrength", "ポップ3D個別強度"),
        ("vibrationStrength", "前景微振動個別強度"),
        ("depthLayerStrength", "Depth多層個別強度"),
        ("trickPortalStrength", "トリックポータル個別強度"),
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
        "uniform float u_enableTrickPortal;",
        "uniform float u_hologramStrength;",
        "uniform float u_reliefStrength;",
        "uniform float u_vibrationStrength;",
        "uniform float u_depthLayerStrength;",
        "uniform float u_trickPortalStrength;",
        "uniform float u_edgeCleanup;",
        "uniform float u_hologramNearSuppression;",
    ]:
        require(uniform in html, f"複合／輪郭処理のshader uniformがありません: {uniform}")
    require("subjectBoundaryAt" not in html, "輪郭だけを抽出して再着色する処理が残っています")
    require("softBlurAt" not in html, "元の合成画像を再サンプルする輪郭ぼかしが残っています")
    require("applyCommonCleanup" not in html, "移動前背景を境界へ混ぜる共通輪郭処理が残っています")
    require("float hologramDepthAttenuation=" in html, "Depthに応じたホログラム強度制御がありません")
    require("u_hologramNearSuppression" in html, "近景ホログラム抑制値をshaderで利用していません")
    for use in [
        "float hologramStrength=clamp(u_hologramStrength",
        "float reliefStrength=clamp(u_reliefStrength",
        "float vibrationStrength=clamp(u_vibrationStrength",
        "float depthLayerStrength=clamp(u_depthLayerStrength",
        "float trickPortalStrength=clamp(u_trickPortalStrength",
    ]:
        require(use in html, f"個別強度をshaderで利用していません: {use}")
    require("float portalInteriorAt(vec2 uv)" in html, "トリックポータル内側の領域判定がありません")
    require("float portalFrameAt(vec2 uv)" in html, "トリックポータルの額縁判定がありません")
    require("vec2 trickPortalBackgroundUV(vec2 uv,float strength)" in html, "背景の透視変形がありません")
    require("portalScene=mix(portalScene,foregroundColor.rgb,foregroundMask);" in html, "前景が額縁を越える合成順序になっていません")
    require("float portalAmount=clamp(u_enableTrickPortal*u_trickPortalStrength" in html, "背後影へポータル強度が反映されていません")
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
    require(
        "vec2 backgroundOffset=u_viewFar*u_depth*layeredDisparity" in html,
        "背景Depthの遠景相対視差がありません",
    )
    require("float whiteHighlight=" in html, "人物／物体の入射光による白飛びがありません")
    require("float surfaceShadow=" in html, "光源と反対側の陰影がありません")
    require("float aerialDepth=" in html, "背景空間の遠方減衰がありません")
    for element_id, label in [
        ("enableSpatial", "裸眼3D強調切替"),
        ("spatialStrength", "空間強調"),
        ("zeroParallax", "ゼロ視差面"),
        ("viewDepth", "前後視点"),
    ]:
        require(f'id="{element_id}"' in html, f"{label}のUIがありません")
    for uniform in [
        "uniform float u_spatialEnhance;",
        "uniform float u_spatialStrength;",
        "uniform float u_zeroParallax;",
        "uniform float u_viewZ;",
    ]:
        require(uniform in html, f"裸眼3D強調のshader uniformがありません: {uniform}")
    require("float depthDisparityAt(float depth)" in html, "ゼロ視差面を基準にした奥行き視差がありません")
    require("depth-u_zeroParallax" in html, "手前と奥を逆方向へ分ける相対視差がありません")
    require("float contactShadowAt(vec2 uv)" in html, "視点連動の被写体背後影がありません")
    require("float spatialWindowShadeAt(vec2 uv)" in html, "画面面を固定する空間ウィンドウ陰影がありません")
    require("float softSubjectMaskAt(vec2 uv)" in html, "移動した被写体輪郭のソフト化がありません")
    require("const leftEye=lm[33],rightEye=lm[263]" in html, "顔サイズから前後位置を求めていません")
    require("faceScaleBaseline" in html and "targetZ=" in html, "顔の接近／離反追跡がありません")
    require("function smoothingFactor(rate,deltaSeconds)" in html, "更新レート非依存の視点追従がありません")
    require("1-Math.exp(-rate*deltaSeconds)" in html, "視点追従が経過時間で正規化されていません")
    require("selfie_multiclass_256x256/float32/1" in html, "固定版の人物部位分離モデルがありません")
    require("ImageSegmenter.createFromOptions" in html, "端末内人物分離の初期化がありません")
    require("function depthForPersonPart(category)" in html, "人物部位別Depth割当がありません")
    require("result.categoryMask.getAsUint8Array()" in html, "人物カテゴリマスクをテクスチャ化していません")
    require("uniform float u_time;" in html, "フレーム同期時刻のshader uniformがありません")
    require("uniform vec2 u_texelSize;" in html, "輪郭検出用texelサイズのshader uniformがありません")
    require("uniform float u_motionScale;" in html, "視差低減用のshader uniformがありません")
    require("imageEdgeAt" not in html, "輪郭再強調に使われる画像エッジ検出が残っています")
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
    require('id="showGuides"' in html, "編集ガイドの表示切替がありません")
    require('!$("#showGuides").checked' in html, "編集ガイドが初期状態で画像へ重なります")
    require("const size=384;" in html, "認識ガイドの輪郭解像度が低すぎます")
    require("function updateRecognitionGuide(source" in html, "認識マスクから編集ガイドを作成していません")
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
    require("subjectMaskAt(" in html[html.index("float contourCropMaskAt") :], "入力マスク／透過立ち絵輪郭をトリミングへ利用していません")
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
    print("PASS: six effect modes including Depth Map layered and Trick Portal 3D")
    print("PASS: stackable effects, common contour cleanup, and near-depth hologram control")
    print("PASS: zero-parallax motion, head-distance zoom, contact shadow, and spatial window cues")
    print("PASS: draggable guides, mask-contour crop, undo/redo, and reset defaults")
    print("PASS: camera-before-MediaPipe ordering")
    print("PASS: pinned MediaPipe dependency and CPU fallback")
    print("PASS: settings panel visibility toggle and accessibility")
    print("PASS: nine demos, stage-fit placement, silhouette auto-rig, and Live2D-style motion")
    print("PASS: Cross-AI governance documents")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, ValueError, subprocess.CalledProcessError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        raise SystemExit(1)
