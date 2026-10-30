#!/usr/bin/env python3
"""人物部位推定の係数を座標降下で探索する（ループ改善の記録用。結果はhuman_parts_lib.DEFAULTSへ反映済み）。"""
from __future__ import annotations

import json
import sys

import human_parts_lib as L

GRID = {
    "skin_delta": [10, 12, 14, 17, 20], "face_pct": [0, 4, 8, 12, 16], "face_scale": [0.8, 0.9, 1.0, 1.12, 1.25], "face_aspect_max": [1.0, 1.15, 1.25, 1.4],
    "hair_delta": [16, 20, 24, 30, 36],
    "waist_t": [0.5, 0.55, 0.6, 0.65, 0.7, 0.76], "waist_rx": [0.3, 0.38, 0.46, 0.55], "waist_ry": [0.06, 0.09, 0.12, 0.16, 0.2],
    "chest_t": [0.2, 0.26, 0.3, 0.36, 0.42], "chest_dx": [0.18, 0.24, 0.3, 0.36], "chest_rx": [0.16, 0.2, 0.24, 0.3], "chest_ry": [0.13, 0.17, 0.19, 0.24],
    "garment_end_frac": [0.3, 0.42, 0.55, 0.7], "garment_x_pct": [0, 1, 2, 4, 8],
    "acc_contrast": [14, 18, 22], "acc_radius": [0.05, 0.07, 0.09],
    "waist_t0": [0.3, 0.4], "waist_t1": [0.7, 0.8], "waist_win": [0.5, 0.6, 0.7], "face_trim": [0, 0.5, 0.6, 0.7, 0.8, 0.9], "waist_t_fine": [0],
    "foot_wx": [0.04, 0.055, 0.07, 0.09], "foot_up": [0.0, 0.02, 0.04], "foot_hy": [0.05, 0.07, 0.10, 0.13], "foot_pct": [0, 2, 5, 10],
}
KEYS = ["face", "face", "hair", "waist", "waist", "chest", "top", "bottom", "accessory_recall", "accessory_recall"]


def objective(params, items):
    row = L.evaluate("", [(a, L.improved_parts(a, params, 5)) for a in items])
    return sum(row[k] for k in KEYS) / len(KEYS) - 0.25 * row["hair_face_leak"], row


def main() -> int:
    items, held_out = L.split_assets(L.load_assets())
    params = dict(L.DEFAULTS)
    best, row = objective(params, items)
    history = [{"pass": 0, "score": round(best, 2), **row}]
    for round_index in range(1, 4):
        changed = False
        for key, values in GRID.items():
            for value in values:
                trial = dict(params, **{key: value})
                score, trial_row = objective(trial, items)
                if score > best + 1e-9:
                    params, best, row, changed = trial, score, trial_row, True
        validation = L.evaluate("val", [(a, L.improved_parts(a, params, 5)) for a in held_out])
        history.append({"pass": round_index, "score": round(best, 2), **row, "val": validation})
        if not changed:
            break
    json.dump({"history": history, "params": params}, sys.stdout, ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
