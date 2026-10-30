#!/usr/bin/env python3
"""人物部位（顔・髪・腰・胸・服・小物）認識のPython参照実装と評価関数。

index.html の inferHumanParts() と同じ手順・係数を保つこと。差分はscripts/ci/web_regression_gateが検査する。
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
POSE_FIXTURE = ROOT / "scripts/ci/fixtures/human_pose_accuracy.json"
AUTO_POSE_FIXTURE = ROOT / "scripts/ci/fixtures/human_pose_auto_demos.json"
PART_FIXTURE = ROOT / "scripts/ci/fixtures/human_parts_reference.json"
GRID_W, GRID_H = 192, 288

# index.html と共有する係数（ループで探索した値）。
DEFAULTS = {
    "skin_delta": 10,
    "face_trim": 0.0,
    "face_pct": 0,
    "foot_wx": 0.09,
    "foot_up": 0.02,
    "foot_hy": 0.1,
    "foot_pct": 2.0,
    "foot_on": 1.0,
    "face_scale": 1.12,
    "face_aspect_max": 1.0,
    "garment_x_pct": 4,
    "garment_end_frac": 0.55,
    "acc_min": 0.0016,
    "acc_max": 0.03,
    "acc_fill": 0.4,
    "acc_radius": 0.07,
    "acc_contrast": 22.0,
    "acc_count": 8,
    "hair_delta": 24,
    "face_window": [
        0.55,
        0.55,
        0.38
    ],
    "waist_t": 0.65,
    "waist_rx": 0.46,
    "waist_ry": 0.12,
    "chest_t": 0.2,
    "chest_dx": 0.3,
    "chest_rx": 0.3,
    "chest_ry": 0.19,
    "waist_sil": 1.0,
    "waist_t0": 0.4,
    "waist_t1": 0.7,
    "waist_win": 0.7,
    "waist_smooth": 5
}


def load_assets():
    poses = json.loads(POSE_FIXTURE.read_text(encoding="utf-8"))["assets"]
    refs = json.loads(PART_FIXTURE.read_text(encoding="utf-8"))["assets"]
    auto = json.loads(AUTO_POSE_FIXTURE.read_text(encoding="utf-8"))["assets"]
    poses = poses + [{"name": f"demo-auto-{key}-foreground.png", "pose": value, "overrides": {}} for key, value in auto.items()]
    items = []
    for asset in poses:
        if asset["name"] not in refs:
            continue
        pose = {k: list(v) for k, v in asset["pose"].items()}
        for name, value in asset["overrides"].items():
            pose[name][:2] = value
        items.append({"name": asset["name"], "pose": pose, "reference": refs[asset["name"]], "image": load_image(asset["name"])})
    return items


def split_assets(items):
    held_out = set(json.loads(PART_FIXTURE.read_text(encoding="utf-8")).get("validation", []))
    return [a for a in items if a["name"] not in held_out], [a for a in items if a["name"] in held_out]


def load_image(name: str) -> np.ndarray:
    image = Image.open(ROOT / "assets/demos" / name).convert("RGBA").resize((GRID_W, GRID_H), Image.LANCZOS)
    return np.asarray(image, dtype=np.float32)


def srgb_to_lab(rgb: np.ndarray) -> np.ndarray:
    c = rgb / 255.0
    c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    x = (c[..., 0] * 0.4124 + c[..., 1] * 0.3576 + c[..., 2] * 0.1805) / 0.95047
    y = c[..., 0] * 0.2126 + c[..., 1] * 0.7152 + c[..., 2] * 0.0722
    z = (c[..., 0] * 0.0193 + c[..., 1] * 0.1192 + c[..., 2] * 0.9505) / 1.08883
    f = lambda t: np.where(t > 0.008856, np.cbrt(t), 7.787 * t + 16 / 116)
    fx, fy, fz = f(x), f(y), f(z)
    return np.stack([116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)], axis=-1)


def pose_pair(a, b):
    return [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2]


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def shape_mask(kind: str, shape, angle: float = 0.0) -> np.ndarray:
    ys, xs = np.mgrid[0:GRID_H, 0:GRID_W]
    px, py = (xs + 0.5) / GRID_W, (ys + 0.5) / GRID_H
    dx, dy = px - shape[0], py - shape[1]
    c, s = math.cos(angle), math.sin(angle)
    lx, ly = (c * dx + s * dy) / max(shape[2], 1e-4), (-s * dx + c * dy) / max(shape[3], 1e-4)
    if kind == "rect":
        return (np.abs(lx) <= 1) & (np.abs(ly) <= 1)
    return lx * lx + ly * ly <= 1


def iou(a: np.ndarray, b: np.ndarray) -> float:
    union = np.count_nonzero(a | b)
    return np.count_nonzero(a & b) / union if union else 0.0


def components(mask: np.ndarray):
    labels = np.zeros(mask.shape, dtype=np.int32)
    count = 0
    for y, x in zip(*np.nonzero(mask)):
        if labels[y, x]:
            continue
        count += 1
        stack = [(y, x)]
        labels[y, x] = count
        while stack:
            cy, cx = stack.pop()
            for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
                if 0 <= ny < mask.shape[0] and 0 <= nx < mask.shape[1] and mask[ny, nx] and not labels[ny, nx]:
                    labels[ny, nx] = count
                    stack.append((ny, nx))
    return labels, count


def largest_near(mask: np.ndarray, point) -> np.ndarray:
    labels, count = components(mask)
    if not count:
        return mask
    px, py = int(point[0] * GRID_W), int(point[1] * GRID_H)
    best, best_score = 0, -1.0
    for index in range(1, count + 1):
        ys, xs = np.nonzero(labels == index)
        near = np.min(np.hypot(xs - px, ys - py))
        score = len(xs) / (1 + near * 0.35)
        if score > best_score:
            best, best_score = index, score
    return labels == best


def bbox_shape(mask: np.ndarray, low: float = 0.0, high: float = 100.0):
    ys, xs = np.nonzero(mask)
    if not len(xs):
        return None
    x0, x1 = np.percentile(xs, [low, high])
    y0, y1 = np.percentile(ys, [low, high])
    x0, x1, y0, y1 = x0 / GRID_W, (x1 + 1) / GRID_W, y0 / GRID_H, (y1 + 1) / GRID_H
    return [(x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2]


def best_kind(mask: np.ndarray, shape) -> str:
    """マスクへ矩形と楕円の両方を当て、IoUの高い形状を選ぶ（部位ごとの形状選択）。"""
    rect, ellipse = iou(shape_mask("rect", shape), mask), iou(shape_mask("ellipse", shape), mask)
    return "rect" if rect >= ellipse else "ellipse"


# ---------- L0: 現行 index.html の buildHumanRigParts と同じ式 ----------
def baseline_parts(asset):
    pose = asset["pose"]
    neck, pelvis = pose_pair(pose["shoulderLeft"], pose["shoulderRight"]), pose_pair(pose["hipLeft"], pose["hipRight"])
    span = dist(pose["shoulderLeft"], pose["shoulderRight"])
    head_top = [pose["nose"][0], max(0.01, pose["nose"][1] - span * 0.38)]
    head_center = pose_pair(head_top, neck)
    head = [head_center[0], head_center[1], max(0.055, span * 0.30), max(0.075, dist(head_top, neck) * 0.58)]
    hair = [head_center[0], head_center[1] + max(0.018, span * 0.08), max(0.065, span * 0.39), max(0.09, dist(head_top, neck) * 0.78)]
    chest_center = [neck[0] + (pelvis[0] - neck[0]) * 0.34, neck[1] + (pelvis[1] - neck[1]) * 0.34]
    chest = [chest_center[0], chest_center[1], max(0.06, span * 0.30), max(0.045, span * 0.19)]
    return {"face": ("ellipse", head), "hair": ("ellipse", hair), "chest": [("ellipse", chest)], "waist": None, "top": None, "bottom": None, "accessories": [],
            "hair_face_overlap_shape": (head, hair)}


# ---------- 改善版 ----------
def build_masks(asset, params):
    image = asset["image"]
    alpha = image[..., 3] > 128
    lab = srgb_to_lab(image[..., :3])
    pose = asset["pose"]
    span = dist(pose["shoulderLeft"], pose["shoulderRight"])
    nx, ny = pose["nose"][0], pose["nose"][1]
    px, py = int(nx * GRID_W), int(ny * GRID_H)
    ys, xs = np.mgrid[0:GRID_H, 0:GRID_W]
    # 肌色の事前分布（アニメ肌）でnose周辺の候補を作り、その中央値を人物固有の肌色にする。
    prior = alpha & (lab[..., 0] > 55) & (lab[..., 1] > 1) & (lab[..., 1] < 28) & (lab[..., 2] > 5) & (lab[..., 2] < 35)
    near = (np.hypot(xs / GRID_W - nx, ys / GRID_H - ny) < span * 0.35) & prior
    skin = np.median(lab[near], axis=0) if np.count_nonzero(near) > 6 else np.array([75.0, 14.0, 18.0])
    skin_like = alpha & (np.linalg.norm(lab - skin, axis=-1) < params["skin_delta"])
    wx, wy_up, wy_dn = params["face_window"]
    window = (np.abs(xs / GRID_W - nx) < wx * span) & (ys / GRID_H > ny - wy_up * span) & (ys / GRID_H < ny + wy_dn * span)
    face = largest_near(skin_like & window, (nx, ny))
    if params["face_trim"] > 0 and np.count_nonzero(face):
        widths = face.sum(axis=1)
        top_row = int(np.nonzero(widths)[0][0])
        peak = int(np.argmax(widths))
        chin = len(widths)
        for row in range(peak, len(widths)):
            if widths[row] < params["face_trim"] * widths[peak]:
                chin = row
                break
        face = face.copy()
        face[chin:] = False
    face_shape = bbox_shape(face, params["face_pct"], 100 - params["face_pct"])
    if face_shape is not None:
        face_shape[2] *= params["face_scale"]
        face_shape[3] = min(face_shape[3] * params["face_scale"], face_shape[2] * params["face_aspect_max"])
    if face_shape is None:
        face_shape = [nx, ny, span * 0.2, span * 0.25]
    top_y = face_shape[1] - face_shape[3]
    fx0, fx1 = face_shape[0] - face_shape[2] * 1.2, face_shape[0] + face_shape[2] * 1.2
    sample = alpha & ~skin_like & (xs / GRID_W > fx0) & (xs / GRID_W < fx1) & (ys / GRID_H > top_y - face_shape[3] * 0.8) & (ys / GRID_H < top_y + face_shape[3] * 0.25)
    hair_color = np.median(lab[sample], axis=0) if np.count_nonzero(sample) > 8 else np.array([30.0, 0.0, 0.0])
    pelvis = pose_pair(pose["hipLeft"], pose["hipRight"])
    hair_like = alpha & (np.linalg.norm(lab - hair_color, axis=-1) < params["hair_delta"]) & (ys / GRID_H < pelvis[1] + 0.16)
    hair = largest_near(hair_like, (face_shape[0], top_y))
    return {"alpha": alpha, "lab": lab, "skin_like": skin_like, "skin": skin, "face": face, "face_shape": face_shape, "hair": hair, "hair_color": hair_color, "span": span}


def torso_frame(pose):
    neck, pelvis = pose_pair(pose["shoulderLeft"], pose["shoulderRight"]), pose_pair(pose["hipLeft"], pose["hipRight"])
    axis = math.atan2(pelvis[1] - neck[1], pelvis[0] - neck[0]) - math.pi / 2
    shoulder_tilt = math.atan2(pose["shoulderLeft"][1] - pose["shoulderRight"][1], pose["shoulderLeft"][0] - pose["shoulderRight"][0])
    return neck, pelvis, axis, shoulder_tilt


def waist_row(alpha, pose, span, params):
    """胴の列帯でシルエット幅が最小になる行を腰の高さとする。"""
    neck, pelvis, _, _ = torso_frame(pose)
    cx = (neck[0] + pelvis[0]) / 2
    columns = np.abs(np.arange(GRID_W) / GRID_W - cx) < params["waist_win"] * span
    first = int((neck[1] + (pelvis[1] - neck[1]) * params["waist_t0"]) * GRID_H)
    last = int((neck[1] + (pelvis[1] - neck[1]) * params["waist_t1"]) * GRID_H)
    if last <= first:
        return None
    widths = alpha[:, columns].sum(axis=1).astype(float)
    smooth = np.convolve(widths, np.ones(int(params["waist_smooth"])) / int(params["waist_smooth"]), mode="same")
    return (first + int(np.argmin(smooth[first:last]))) / GRID_H


def waist_chest(pose, span, params, alpha=None):
    neck, pelvis, axis, tilt = torso_frame(pose)
    waist_c = [neck[0] + (pelvis[0] - neck[0]) * params["waist_t"], neck[1] + (pelvis[1] - neck[1]) * params["waist_t"]]
    if alpha is not None and params.get("waist_sil"):
        row = waist_row(alpha, pose, span, params)
        if row is not None:
            waist_c[1] = row
    waist = [waist_c[0], waist_c[1], span * params["waist_rx"], span * params["waist_ry"]]
    chest_c = [neck[0] + (pelvis[0] - neck[0]) * params["chest_t"], neck[1] + (pelvis[1] - neck[1]) * params["chest_t"]]
    side = [math.cos(tilt), math.sin(tilt)]
    left = [chest_c[0] + side[0] * span * params["chest_dx"], chest_c[1] + side[1] * span * params["chest_dx"], span * params["chest_rx"], span * params["chest_ry"]]
    right = [chest_c[0] - side[0] * span * params["chest_dx"], chest_c[1] - side[1] * span * params["chest_dx"], span * params["chest_rx"], span * params["chest_ry"]]
    return waist, [left, right], tilt


def garment_regions(asset, masks, waist, params):
    span = masks["span"]
    pose = asset["pose"]
    garment = masks["alpha"] & ~masks["skin_like"] & ~masks["hair"]
    neck = pose_pair(pose["shoulderLeft"], pose["shoulderRight"])
    shoulder_y = min(pose["shoulderLeft"][1], pose["shoulderRight"][1])
    waist_row = int(waist[1] * GRID_H)
    top_rows = slice(max(0, int(shoulder_y * GRID_H)), max(1, waist_row))
    result = {}
    ys, xs = np.nonzero(garment[top_rows])
    if len(xs):
        ys = ys + top_rows.start
        x0, x1 = np.percentile(xs, [params["garment_x_pct"], 100 - params["garment_x_pct"]])
        y0, y1 = shoulder_y, waist[1]
        result["top"] = ("rect", [(x0 + x1 + 1) / 2 / GRID_W, (y0 + y1) / 2, (x1 - x0 + 1) / 2 / GRID_W, (y1 - y0) / 2])
    band = garment[waist_row:]
    widths = band.sum(axis=1)
    reach = widths[: max(3, int(0.10 * GRID_H))].max() if len(widths) else 0
    end = len(widths)
    for row in range(len(widths) - 3):
        if row > 3 and widths[row:row + 3].max() < params["garment_end_frac"] * reach:
            end = row
            break
    ys, xs = np.nonzero(band[:max(1, end)])
    if len(xs):
        x0, x1 = np.percentile(xs, [params["garment_x_pct"], 100 - params["garment_x_pct"]])
        y0, y1 = waist[1], (waist_row + end) / GRID_H
        result["bottom"] = ("rect", [(x0 + x1 + 1) / 2 / GRID_W, (y0 + y1) / 2, (x1 - x0 + 1) / 2 / GRID_W, (y1 - y0) / 2])
    return result


def box_blur(values: np.ndarray, radius: int) -> np.ndarray:
    pad = np.pad(values, ((radius + 1, radius), (radius + 1, radius), (0, 0)), mode="edge")
    csum = pad.cumsum(axis=0).cumsum(axis=1)
    size = 2 * radius + 1
    total = csum[size:, size:] - csum[:-size, size:] - csum[size:, :-size] + csum[:-size, :-size]
    return total[: values.shape[0], : values.shape[1]] / (size * size)


def accessory_blobs(asset, masks, params):
    """局所コントラストの高い小さな塊を小物候補にする（色クラスタではなく周囲との差）。"""
    lab, alpha = masks["lab"], masks["alpha"]
    candidate = alpha & ~masks["skin_like"] & ~masks["hair"]
    weight = candidate.astype(np.float32)[..., None]
    radius = max(3, int(GRID_W * params["acc_radius"]))
    local = box_blur(lab * weight, radius) / np.maximum(box_blur(weight, radius), 1e-3)
    saliency = np.linalg.norm(lab - local, axis=-1) * candidate
    total = max(1, np.count_nonzero(alpha))
    threshold = max(params["acc_contrast"], 0)
    salient = saliency > threshold
    labels, count = components(salient)
    blobs = []
    for index in range(1, count + 1):
        component = labels == index
        area = np.count_nonzero(component) / total
        if not (params["acc_min"] <= area <= params["acc_max"]):
            continue
        shape = bbox_shape(component, 0, 100)
        fill = np.count_nonzero(component) / max(1, (shape[2] * GRID_W * 2) * (shape[3] * GRID_H * 2))
        if fill >= params["acc_fill"]:
            blobs.append((float(saliency[component].mean()) * math.sqrt(area), ("ellipse" if best_kind(component, shape) == "ellipse" else "rect", shape)))
    blobs.sort(key=lambda item: -item[0])
    return [shape for _, shape in blobs[: params["acc_count"]]]


def foot_boxes(asset, masks, params):
    alpha, pose = masks["alpha"], asset["pose"]
    boxes = []
    for name in ("ankleLeft", "ankleRight"):
        ax, ay = pose[name][0], pose[name][1]
        ys, xs = np.mgrid[0:GRID_H, 0:GRID_W]
        window = alpha & (np.abs(xs / GRID_W - ax) < params["foot_wx"]) & (ys / GRID_H > ay - params["foot_up"]) & (ys / GRID_H < ay + params["foot_hy"])
        if np.count_nonzero(window) < 12:
            continue
        shape = bbox_shape(window, params["foot_pct"], 100 - params["foot_pct"])
        boxes.append((best_kind(window, shape), shape))
    return boxes


def improved_parts(asset, params, level):
    base = baseline_parts(asset)
    parts = {k: base[k] for k in ("face", "hair", "chest", "waist", "top", "bottom", "accessories")}
    pose = asset["pose"]
    masks = build_masks(asset, params) if level >= 2 else None
    span = dist(pose["shoulderLeft"], pose["shoulderRight"])
    if level >= 1:
        waist, chests, tilt = waist_chest(pose, span, params, asset["image"][..., 3] > 128)
        parts["waist"] = ("ellipse", waist)
        parts["chest"] = [("ellipse", chests[0]), ("ellipse", chests[1])]
    if level >= 2:
        parts["face"] = ("ellipse", masks["face_shape"])
        hair_shape = bbox_shape(masks["hair"], 0.5, 99.5)
        if hair_shape:
            parts["hair"] = ("ellipse", hair_shape)
    if level >= 3:
        # 部位ごとに矩形/楕円を選ぶ。
        for key in ("waist",):
            parts[key] = (best_kind(masks["alpha"], parts[key][1]) if False else "rect", parts[key][1])
        if masks and np.count_nonzero(masks["hair"]):
            parts["hair"] = (best_kind(masks["hair"], parts["hair"][1]), parts["hair"][1])
    if level >= 4:
        parts.update(garment_regions(asset, masks, parts["waist"][1], params))
    if level >= 5:
        parts["accessories"] = (foot_boxes(asset, masks, params) if params["foot_on"] else []) + accessory_blobs(asset, masks, params)
    parts["hair_excludes_face"] = level >= 2
    return parts


def part_iou(kind_shape, ref) -> float:
    if kind_shape is None:
        return 0.0
    return iou(shape_mask(*kind_shape), shape_mask(ref["kind"], ref["shape"]))


def evaluate(label, predictions):
    scores = {"face": [], "hair": [], "waist": [], "chest": [], "top": [], "bottom": [], "accessory_recall": [], "accessory_precision": []}
    leak = []
    for (asset, parts) in predictions:
        ref = asset["reference"]
        scores["face"].append(part_iou(parts["face"], ref["face"]))
        scores["hair"].append(part_iou(parts["hair"], ref["hair"]))
        scores["waist"].append(part_iou(parts["waist"], ref["waist"]))
        for target in ref["chest"]:
            candidates = parts["chest"]
            scores["chest"].append(max([part_iou(c, target) for c in candidates] or [0.0]))
        scores["top"].append(part_iou(parts["top"], ref["top"]))
        scores["bottom"].append(part_iou(parts["bottom"], ref["bottom"]))
        accessories = parts["accessories"]
        matched = [max([part_iou(c, r) for c in accessories] or [0.0]) for r in ref["accessories"]]
        scores["accessory_recall"].append(np.mean([m >= 0.25 for m in matched]))
        used = [max([part_iou(c, r) for r in ref["accessories"]] or [0.0]) for c in accessories]
        scores["accessory_precision"].append(np.mean([u >= 0.25 for u in used]) if used else 0.0)
        # 髪が顔の正解範囲へかかる割合（髪アニメーションの顔への漏れ。小さいほど良い）。
        hair_mask, face_ref = shape_mask(*parts["hair"]), shape_mask(ref["face"]["kind"], ref["face"]["shape"])
        if parts.get("hair_excludes_face"):
            hair_mask = hair_mask & ~shape_mask(*parts["face"])
        leak.append(np.count_nonzero(hair_mask & face_ref) / max(1, np.count_nonzero(face_ref)))
    row = {"loop": label, **{k: round(float(np.mean(v)) * 100, 1) for k, v in scores.items()}, "hair_face_leak": round(float(np.mean(leak)) * 100, 1)}
    return row
