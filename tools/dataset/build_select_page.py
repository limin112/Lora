"""生成 Moss 训练数据挑选页面 select_page/index.html。

扫描第一批 M01–M48（virtual_person/M*.png）和补拍 supplement/raw/P??_*.png，
用两份清单预填 caption 字段。补拍图生成后重新运行即可；浏览器里已做的选择按镜头编号保留。

usage: python3 build_select_page.py
"""
import csv
import json
import re
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent
PAGE = ROOT / "select_page"
(PAGE / "img").mkdir(parents=True, exist_ok=True)
TRIGGER = "moss01"
ANGLE_CHOICES = ["front view", "front view, high camera angle", "front view, low camera angle",
                 "three-quarter view facing left", "three-quarter view facing right",
                 "side profile facing left", "side profile facing right", "back view, looking over shoulder",
                 "back view"]


def normalize_angle(text: str) -> str:
    """把补拍清单里的角度描述对应到下拉框选项。"""
    t = text.lower()
    if "behind" in t or "back" in t:
        return "back view, looking over shoulder" if ("over" in t or "looking back" in t) else "back view"
    if "side profile" in t:
        return "side profile facing left" if "left" in t else "side profile facing right"
    if "three-quarter" in t:
        return "three-quarter view facing left" if "left" in t else "three-quarter view facing right"
    if "high angle" in t or "above eye level" in t:
        return "front view, high camera angle"
    if "low camera" in t or "low angle" in t:
        return "front view, low camera angle"
    return "front view"


def thumb(src: Path) -> str:
    out = PAGE / "img" / (src.stem + ".jpg")
    if not out.exists() or out.stat().st_mtime < src.stat().st_mtime:
        im = Image.open(src).convert("RGB")
        im.thumbnail((640, 640))
        im.save(out, quality=85)
    return f"img/{out.name}"


def hair_from_caption(caption: str) -> str:
    m = re.search(r"hairstyle: ([^,]+)", caption)
    return m.group(1) if m else ""


shots = []
for r in csv.DictReader(open(ROOT / "moss_shotlist.csv", encoding="utf-8")):
    f = ROOT / f"{r['id']}.png"
    if not f.exists():
        continue
    shots.append({
        "id": r["id"], "batch": "第一批",
        "candidates": [{"file": f"../{f.name}", "thumb": thumb(f), "name": f.name}],
        "fields": {"framing": r["framing"], "angle": "",            # 第一批的角度清单不可信，必须看图选
                   "expression": r["expression"], "hair": hair_from_caption(r["caption"]),
                   "outfit": r["outfit"], "scene": r["scene"], "lighting": r["lighting"]},
        "check": "角度请按图选择（清单里的角度多数与图不符）",
    })

SUP_DIRS = [ROOT / "supplement" / "raw", ROOT / "supplement" / "generated_gpt_image2"]
sup_csv = ROOT / "supplement" / "moss_supplement_shotlist.csv"
for r in csv.DictReader(open(sup_csv, encoding="utf-8")):
    files = sorted(f for d in SUP_DIRS if d.exists() for f in d.iterdir()
                   if f.suffix.lower() in {".png", ".jpg", ".jpeg"} and f.name.lower().startswith(r["id"].lower() + "_"))
    if not files:
        continue
    shots.append({
        "id": r["id"], "batch": "补拍",
        "candidates": [{"file": f"../{f.relative_to(ROOT).as_posix()}", "thumb": thumb(f), "name": f.name} for f in files],
        "fields": {"framing": r["framing"], "angle": normalize_angle(r["angle"]),
                   "expression": r["expression"], "hair": r["hair"], "outfit": r["outfit"],
                   "scene": r["scene"], "lighting": r["lighting"]},
        "check": "验收：" + r["check"],
    })

# Claude 看图后的建议（make_claude_suggestions.py 生成）：作为页面默认值，人工可改
sug_file = ROOT / "claude_suggestions.json"
suggestions = json.loads(sug_file.read_text(encoding="utf-8")) if sug_file.exists() else {}
for s in shots:
    g = suggestions.get(s["id"])
    if not g:
        s["suggest"] = None
        continue
    s["fields"].update(g["fields"])
    s["suggest"] = {"pick": s["candidates"][0]["name"] if g["use"] else None, "drop": not g["use"], "note": g["note"]}

data = {"trigger": TRIGGER, "angles": ANGLE_CHOICES, "shots": shots}
html = (ROOT / "select_page_template.html").read_text(encoding="utf-8")
(PAGE / "index.html").write_text(html.replace("__DATA__", json.dumps(data, ensure_ascii=False)), encoding="utf-8")
n_img = sum(len(s["candidates"]) for s in shots)
print(f"wrote {PAGE / 'index.html'}: {len(shots)} shots, {n_img} images "
      f"({sum(s['batch'] == '第一批' for s in shots)} 第一批, {sum(s['batch'] == '补拍' for s in shots)} 补拍)")
