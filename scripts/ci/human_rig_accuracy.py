#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "scripts/ci/fixtures/human_pose_accuracy.json"
PART_NAMES = ["head", "armLeft", "armRight", "handLeft", "handRight", "upperBody", "legLeft", "legRight"]
BONE_NAMES = ["pelvis", "spine", "neck", "headTop", "shoulderLeft", "elbowLeft", "wristLeft", "shoulderRight", "elbowRight", "wristRight", "hipLeft", "kneeLeft", "ankleLeft", "hipRight", "kneeRight", "ankleRight"]


def midpoint(a: list[float], b: list[float]) -> list[float]:
    return [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2]


def distance(a: list[float], b: list[float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def bones_from_pose(pose: dict[str, list[float]]) -> dict[str, list[float]]:
    shoulders = midpoint(pose["shoulderLeft"], pose["shoulderRight"])
    pelvis = midpoint(pose["hipLeft"], pose["hipRight"])
    span = distance(pose["shoulderLeft"], pose["shoulderRight"])
    head_top = [pose["nose"][0], max(0.01, pose["nose"][1] - span * 0.38)]
    return {
        "pelvis": pelvis,
        "spine": midpoint(shoulders, pelvis),
        "neck": shoulders,
        "headTop": head_top,
        "shoulderLeft": pose["shoulderLeft"][:2], "elbowLeft": pose["elbowLeft"][:2], "wristLeft": pose["wristLeft"][:2],
        "shoulderRight": pose["shoulderRight"][:2], "elbowRight": pose["elbowRight"][:2], "wristRight": pose["wristRight"][:2],
        "hipLeft": pose["hipLeft"][:2], "kneeLeft": pose["kneeLeft"][:2], "ankleLeft": pose["ankleLeft"][:2],
        "hipRight": pose["hipRight"][:2], "kneeRight": pose["kneeRight"][:2], "ankleRight": pose["ankleRight"][:2],
    }


def reference_bones(reference: dict[str, list[float]]) -> dict[str, list[float]]:
    shoulders = midpoint(reference["shoulderLeft"], reference["shoulderRight"])
    pelvis = midpoint(reference["hipLeft"], reference["hipRight"])
    return {
        "pelvis": pelvis,
        "spine": midpoint(shoulders, pelvis),
        "neck": shoulders,
        "headTop": reference["headTop"],
        **{name: reference[name] for name in BONE_NAMES if name in reference},
    }


def oriented_region(points: list[list[float]], padding: float, minimum_minor: float) -> dict[str, float]:
    center = [sum(point[0] for point in points) / len(points), sum(point[1] for point in points) / len(points)]
    xx = sum((point[0] - center[0]) ** 2 for point in points)
    yy = sum((point[1] - center[1]) ** 2 for point in points)
    xy = sum((point[0] - center[0]) * (point[1] - center[1]) for point in points)
    line_angle = 0.5 * math.atan2(2 * xy, xx - yy)
    major = [math.cos(line_angle), math.sin(line_angle)]
    minor = [-major[1], major[0]]
    major_values = [point[0] * major[0] + point[1] * major[1] for point in points]
    minor_values = [point[0] * minor[0] + point[1] * minor[1] for point in points]
    major_center = (min(major_values) + max(major_values)) / 2
    minor_center = (min(minor_values) + max(minor_values)) / 2
    center = [major[0] * major_center + minor[0] * minor_center, major[1] * major_center + minor[1] * minor_center]
    return {
        "x": center[0], "y": center[1],
        "rx": max(minimum_minor, (max(minor_values) - min(minor_values)) / 2 + padding * 0.55),
        "ry": max(minimum_minor * 1.4, (max(major_values) - min(major_values)) / 2 + padding),
        "angle": line_angle - math.pi / 2,
    }


def oriented_parts(bones: dict[str, list[float]]) -> dict[str, dict[str, float]]:
    shoulder_span = distance(bones["shoulderLeft"], bones["shoulderRight"])
    head_center = midpoint(bones["headTop"], bones["neck"])
    head_axis = math.atan2(bones["neck"][1] - bones["headTop"][1], bones["neck"][0] - bones["headTop"][0]) - math.pi / 2
    head = {"x": head_center[0], "y": head_center[1], "rx": max(0.055, shoulder_span * 0.30), "ry": max(0.075, distance(bones["headTop"], bones["neck"]) * 0.58), "angle": head_axis}
    upper = oriented_region([bones["shoulderLeft"], bones["shoulderRight"], bones["hipLeft"], bones["hipRight"]], 0.035, 0.07)
    return {
        "head": head,
        "armLeft": oriented_region([bones["shoulderLeft"], bones["elbowLeft"], bones["wristLeft"]], 0.032, 0.045),
        "armRight": oriented_region([bones["shoulderRight"], bones["elbowRight"], bones["wristRight"]], 0.032, 0.045),
        "handLeft": {"x": bones["wristLeft"][0], "y": bones["wristLeft"][1], "rx": 0.045, "ry": 0.058, "angle": 0},
        "handRight": {"x": bones["wristRight"][0], "y": bones["wristRight"][1], "rx": 0.045, "ry": 0.058, "angle": 0},
        "upperBody": upper,
        "legLeft": oriented_region([bones["hipLeft"], bones["kneeLeft"], bones["ankleLeft"]], 0.038, 0.055),
        "legRight": oriented_region([bones["hipRight"], bones["kneeRight"], bones["ankleRight"]], 0.038, 0.055),
    }


def baseline(asset: dict[str, object]) -> tuple[dict[str, list[float]], dict[str, dict[str, float]]]:
    left, top, width, height = asset["alphaBounds"]
    center_x = left + width / 2
    ground = min(0.995, top + height)
    head = [center_x, top + height * 0.17, min(width * 0.28, 0.25), min(height * 0.17, 0.19)]
    body = [center_x, top + height * 0.52, min(width * 0.34, 0.34), min(height * 0.40, 0.34)]
    body_y, body_rx, body_ry = body[1], body[2], body[3]
    shoulder_y = body_y - body_ry * 0.42
    hand_y = min(ground - 0.13, body_y + body_ry * 0.48)
    arm_y = (shoulder_y + hand_y) / 2
    arm_offset = max(0.085, body_rx * 0.88)
    hand_offset = max(0.12, body_rx * 1.18)
    hip_y = min(ground - 0.18, body_y + body_ry * 0.58)
    leg_y = (hip_y + ground - 0.015) / 2
    leg_offset = max(0.045, body_rx * 0.34)
    parts = {
        "head": {"x": head[0], "y": head[1], "rx": head[2], "ry": head[3], "angle": 0},
        "armLeft": {"x": center_x + arm_offset, "y": arm_y, "rx": max(0.05, body_rx * 0.42), "ry": max(0.09, (hand_y - shoulder_y) * 0.62), "angle": 0},
        "armRight": {"x": center_x - arm_offset, "y": arm_y, "rx": max(0.05, body_rx * 0.42), "ry": max(0.09, (hand_y - shoulder_y) * 0.62), "angle": 0},
        "handLeft": {"x": center_x + hand_offset, "y": hand_y, "rx": max(0.035, body_rx * 0.25), "ry": max(0.04, body_ry * 0.16), "angle": 0},
        "handRight": {"x": center_x - hand_offset, "y": hand_y, "rx": max(0.035, body_rx * 0.25), "ry": max(0.04, body_ry * 0.16), "angle": 0},
        "upperBody": {"x": center_x, "y": body_y, "rx": max(0.09, body_rx * 0.82), "ry": max(0.12, body_ry * 0.72), "angle": 0},
        "legLeft": {"x": center_x + leg_offset, "y": leg_y, "rx": max(0.045, body_rx * 0.34), "ry": max(0.10, (ground - hip_y) * 0.53), "angle": 0},
        "legRight": {"x": center_x - leg_offset, "y": leg_y, "rx": max(0.045, body_rx * 0.34), "ry": max(0.10, (ground - hip_y) * 0.53), "angle": 0},
    }
    pelvis_y = min(ground - 0.16, parts["upperBody"]["y"] + parts["upperBody"]["ry"] * 0.58)
    neck_y = max(parts["head"]["y"] + parts["head"]["ry"] * 0.72, parts["upperBody"]["y"] - parts["upperBody"]["ry"] * 0.72)
    bones = {
        "pelvis": [center_x, pelvis_y], "spine": [center_x, body_y], "neck": [head[0], neck_y], "headTop": [head[0], max(0.02, head[1] - head[3] * 0.72)],
        "shoulderLeft": [center_x + parts["upperBody"]["rx"] * 0.72, shoulder_y], "elbowLeft": [parts["armLeft"]["x"], parts["armLeft"]["y"]], "wristLeft": [parts["handLeft"]["x"], parts["handLeft"]["y"]],
        "shoulderRight": [center_x - parts["upperBody"]["rx"] * 0.72, shoulder_y], "elbowRight": [parts["armRight"]["x"], parts["armRight"]["y"]], "wristRight": [parts["handRight"]["x"], parts["handRight"]["y"]],
        "hipLeft": [parts["legLeft"]["x"], min(ground - 0.12, pelvis_y + 0.025)], "kneeLeft": [parts["legLeft"]["x"], parts["legLeft"]["y"]], "ankleLeft": [parts["legLeft"]["x"], min(0.98, ground - 0.012)],
        "hipRight": [parts["legRight"]["x"], min(ground - 0.12, pelvis_y + 0.025)], "kneeRight": [parts["legRight"]["x"], parts["legRight"]["y"]], "ankleRight": [parts["legRight"]["x"], min(0.98, ground - 0.012)],
    }
    return bones, parts


def ellipse_contains(region: dict[str, float], x: float, y: float) -> bool:
    cosine, sine = math.cos(region["angle"]), math.sin(region["angle"])
    dx, dy = x - region["x"], y - region["y"]
    local_x = cosine * dx + sine * dy
    local_y = -sine * dx + cosine * dy
    return (local_x / region["rx"]) ** 2 + (local_y / region["ry"]) ** 2 <= 1


def ellipse_iou(a: dict[str, float], b: dict[str, float], resolution: int = 180) -> float:
    intersection = union = 0
    for yi in range(resolution):
        y = (yi + 0.5) / resolution
        for xi in range(resolution):
            x = (xi + 0.5) / resolution
            inside_a, inside_b = ellipse_contains(a, x, y), ellipse_contains(b, x, y)
            intersection += inside_a and inside_b
            union += inside_a or inside_b
    return intersection / union if union else 1


def evaluate(label: str, predictions: list[tuple[dict[str, list[float]], dict[str, dict[str, float]], dict[str, list[float]]]]) -> dict[str, float | str]:
    bone_errors, part_errors, ious = [], [], []
    for bones, parts, reference in predictions:
        reference_height = max(point[1] for point in reference.values()) - min(point[1] for point in reference.values())
        for name in BONE_NAMES:
            bone_errors.append(distance(bones[name], reference[name]) / reference_height)
        reference_parts = oriented_parts(reference)
        for name in PART_NAMES:
            part_errors.append(distance([parts[name]["x"], parts[name]["y"]], [reference_parts[name]["x"], reference_parts[name]["y"]]) / reference_height)
            ious.append(ellipse_iou(parts[name], reference_parts[name]))
    return {
        "loop": label,
        "bone_error_percent": round(sum(bone_errors) / len(bone_errors) * 100, 2),
        "bone_pck_5_percent": round(sum(error <= 0.05 for error in bone_errors) / len(bone_errors) * 100, 1),
        "part_center_error_percent": round(sum(part_errors) / len(part_errors) * 100, 2),
        "part_iou_percent": round(sum(ious) / len(ious) * 100, 1),
    }


def main() -> int:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    loops: dict[str, list[tuple[dict[str, list[float]], dict[str, dict[str, float]], dict[str, list[float]]]]] = {"L0 symmetric alpha template": [], "L1 raw pose + axis-aligned regions": [], "L2 raw pose + oriented regions": [], "L3 confidence/outlier calibration + oriented regions": []}
    for asset in fixture["assets"]:
        reference = reference_bones(asset["reference"])
        base_bones, base_parts = baseline(asset)
        loops["L0 symmetric alpha template"].append((base_bones, base_parts, reference))
        raw_bones = bones_from_pose(asset["pose"])
        raw_oriented = oriented_parts(raw_bones)
        raw_axis = {name: {**region, "angle": 0} for name, region in raw_oriented.items()}
        loops["L1 raw pose + axis-aligned regions"].append((raw_bones, raw_axis, reference))
        loops["L2 raw pose + oriented regions"].append((raw_bones, raw_oriented, reference))
        corrected_pose = {name: list(value) for name, value in asset["pose"].items()}
        for name, value in asset["overrides"].items():
            corrected_pose[name][:2] = value
        corrected_bones = bones_from_pose(corrected_pose)
        loops["L3 confidence/outlier calibration + oriented regions"].append((corrected_bones, oriented_parts(corrected_bones), reference))
    metrics = [evaluate(label, predictions) for label, predictions in loops.items()]
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    baseline_metrics, final_metrics = metrics[0], metrics[-1]
    if final_metrics["bone_error_percent"] >= baseline_metrics["bone_error_percent"]:
        raise SystemExit("bone error did not improve")
    if final_metrics["part_iou_percent"] <= baseline_metrics["part_iou_percent"]:
        raise SystemExit("part IoU did not improve")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
