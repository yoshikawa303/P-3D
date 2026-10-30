#!/usr/bin/env python3
"""重なる部位の影響を合計で割る補正（シェーダーのpartInfluenceSum）が、波打ち（二重加算と急な勾配）をどれだけ減らすかを模擬測定する。"""
from __future__ import annotations

import json
import numpy as np

import human_parts_lib as L


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def influence(kind: str, shape) -> np.ndarray:
    ys, xs = np.mgrid[0:L.GRID_H, 0:L.GRID_W]
    lx, ly = ((xs + .5) / L.GRID_W - shape[0]) / shape[2], ((ys + .5) / L.GRID_H - shape[1]) / shape[3]
    norm = np.maximum(np.abs(lx), np.abs(ly)) * 0 + (np.abs(lx) ** 4 + np.abs(ly) ** 4) ** .25 if kind == "rect" else np.hypot(lx, ly)
    return 1 - smoothstep(.62, 1.04, norm)


def main() -> int:
    rows = []
    for asset in L.load_assets():
        parts = L.improved_parts(asset, L.DEFAULTS, 5)
        shapes = [parts["face"], parts["hair"], parts["waist"], *parts["chest"], parts["top"], parts["bottom"]]
        shapes = [s for s in shapes if s]
        alpha = asset["image"][..., 3] > 128
        # 部位ごとに別方向の動き（最悪ケース: 重なりで同方向に足し合わさる）。
        directions = [np.array([np.cos(i * 1.3), np.sin(i * 1.3)]) for i in range(len(shapes))]
        weights = np.stack([influence(*s) for s in shapes])
        raw = sum(w[..., None] * d for w, d in zip(weights, directions))
        total = weights.sum(axis=0)
        fixed = raw / np.maximum(1, total)[..., None]
        def rough(field):
            gy, gx = np.gradient(field, axis=(0, 1))
            return float(np.hypot(gx, gy)[alpha].mean())
        rows.append({"asset": asset["name"], "overlap_px_percent": round(float((total[alpha] > 1).mean() * 100), 1),
                     "max_disp_before": round(float(np.linalg.norm(raw, axis=-1)[alpha].max()), 2), "max_disp_after": round(float(np.linalg.norm(fixed, axis=-1)[alpha].max()), 2),
                     "gradient_before": round(rough(raw), 4), "gradient_after": round(rough(fixed), 4)})
    print(json.dumps(rows, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
