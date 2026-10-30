#!/usr/bin/env python3
"""index.html の analyzeHumanParts（JS）が human_parts_lib（Python参照実装）と同じ部位を返すか検査する。"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import human_parts_lib as L

ROOT = Path(__file__).resolve().parents[2]
MIN_IOU = 0.9


def extract_js() -> str:
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    start = html.index("function poseMidpoint")
    first_end = html.index("\n", start)
    distance_start = html.index("function poseDistance")
    distance_end = html.index("\n", distance_start)
    block_start = html.index("const HUMAN_PARTS_GRID")
    block_end = html.index("async function analyzeHumanPartsFromSource")
    return html[start:first_end] + "\n" + html[distance_start:distance_end] + "\n" + html[block_start:block_end]


def main() -> int:
    node = shutil.which("node")
    if not node:
        print("node がないためJS/Python一致検査をスキップします")
        return 0
    items = L.load_assets()
    payload = [{"pose": item["pose"], "rgba": item["image"].astype(int).reshape(-1).tolist()} for item in items]
    with tempfile.TemporaryDirectory() as directory:
        data_path, script_path = Path(directory) / "data.json", Path(directory) / "run.js"
        data_path.write_text(json.dumps(payload), encoding="utf-8")
        script_path.write_text(extract_js() + f"""
const items=JSON.parse(require('fs').readFileSync({json.dumps(str(data_path))},'utf8'));
const out=items.map(item=>{{const r=analyzeHumanParts(Uint8ClampedArray.from(item.rgba),item.pose);return {{face:r.face,hair:r.hair,garments:r.garments,accessories:r.accessories,torso:r.torso}}}});
console.log(JSON.stringify(out));
""", encoding="utf-8")
        result = subprocess.run([node, str(script_path)], capture_output=True, text=True, check=True)
    js_results = json.loads(result.stdout)
    worst = 1.0
    for item, js in zip(items, js_results):
        py = L.improved_parts(item, L.DEFAULTS, 5)
        pairs = [("face", py["face"], js["face"]), ("hair", py["hair"], js["hair"])]
        for key in ("top", "bottom"):
            if key in py and key in js["garments"]:
                pairs.append((key, py[key], js["garments"][key]))
            elif key in py or key in js["garments"]:
                raise SystemExit(f"{item['name']}: {key} の有無がJSとPythonで異なります")
        if len(py["accessories"]) != len(js["accessories"]):
            raise SystemExit(f"{item['name']}: 小物数がJS {len(js['accessories'])} / Python {len(py['accessories'])}")
        for index, (a, b) in enumerate(zip(py["accessories"], js["accessories"])):
            pairs.append((f"accessory{index}", a, (b["kind"], b["shape"])))
        for key, expected, actual in pairs:
            actual_pair = (actual["kind"], actual["shape"]) if isinstance(actual, dict) else actual
            score = L.iou(L.shape_mask(*expected), L.shape_mask(*actual_pair))
            worst = min(worst, score)
            if score < MIN_IOU:
                raise SystemExit(f"{item['name']}: {key} のJS/Python一致IoU {score:.3f} < {MIN_IOU}")
    print(json.dumps({"js_python_min_iou": round(worst, 4)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
