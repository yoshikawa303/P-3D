#!/usr/bin/env python3
"""髪/顔・腰・左右の胸・服・小物の認識精度をL0（現行）〜L5（改善後）で定量測定する。"""
from __future__ import annotations

import json

import human_parts_lib as L

LOOPS = [
    ("L0 現行（顔=頭楕円・髪=頭周辺楕円・胸1個）", 0),
    ("L1 腰（胴の最小幅の行）・左右の胸を姿勢の軸から配置", 1),
    ("L2 肌色/髪色の画像解析で顔と髪を分離し、髪から顔を除外", 2),
    ("L3 部位ごとに矩形/楕円を自動選択", 3),
    ("L4 服（上衣・下衣）を非肌・非髪の領域とシルエット幅から推定", 4),
    ("L5 小物を足元（足首周辺の外接）と局所コントラストの塊として検出", 5),
]


def main() -> int:
    items = L.load_assets()
    rows = []
    for label, level in LOOPS:
        rows.append(L.evaluate(label, [(a, L.baseline_parts(a) if level == 0 else L.improved_parts(a, L.DEFAULTS, level)) for a in items]))
    train, held_out = L.split_assets(items)
    splits = {}
    for name, subset in (("train", train), ("held_out", held_out)):
        splits[name] = {"baseline": L.evaluate("L0", [(a, L.baseline_parts(a)) for a in subset]), "final": L.evaluate("L5", [(a, L.improved_parts(a, L.DEFAULTS, 5)) for a in subset]), "assets": len(subset)}
    rows[-1]["splits"] = splits
    print(json.dumps(rows, ensure_ascii=False, indent=2))
    first, last = rows[0], rows[-1]
    for key in ("face", "hair", "waist", "chest", "top", "bottom", "accessory_recall"):
        if last[key] <= first[key]:
            raise SystemExit(f"{key} did not improve")
    if last["hair_face_leak"] >= first["hair_face_leak"]:
        raise SystemExit("hair/face leak did not improve")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
