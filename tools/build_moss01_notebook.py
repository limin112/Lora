"""Generate prepare_moss01_for_lora.ipynb (run once; afterwards edit the notebook directly)."""
import sys
from pathlib import Path

import nbformat as nbf

md = nbf.v4.new_markdown_cell
code = nbf.v4.new_code_cell

cells = [
    md("""# 虚拟人 Moss（moss01）→ MOSS-Image 人物 LoRA 训练集

学习用途实验（第二版）：原创虚构人物，用 Codex（gpt-image-2）以 `ref_face_17.png` 为参考图生成。本 Notebook 按人工确认的 `selection.json` 生成 KohakuMoss 用的 kohya 风格训练目录，并做校验和统计。

复现（在工具包根目录下）：

```bash
.venv/bin/jupyter nbconvert --to notebook --execute --inplace prepare_moss01_for_lora.ipynb
```

路径用环境变量配置，默认值对应工具包的目录结构：`MOSS_PROJECT`（默认 `data/moss01`，里面的 `source/` 放候选图和 `selection.json`）。

数据来源与流程：

1. 第一批 M01–M48：`source/moss_shotlist.csv` 的 48 个镜头，每个 1 张。
2. 补拍 P01–P20：`source/supplement/moss_supplement_shotlist.csv`，针对第一批的缺口（侧脸、背影、表情、便装、全身姿势）。
3. 挑选页面（`build_select_page.py`）预填 Claude 的看图建议（`claude_suggestions.json`），人工复核后导出 `selection.json`：用 56 张，不用 12 张（近重复）。
4. caption 由 7 个字段拼成（构图、角度、表情/动作、发型、服装、场景、光线），按图实际内容填写，不照搬生成清单。

已知数据特点：校服约占 79%（服装绑定风险，评估时专门测）；朝右的角度远多于朝左；真侧脸特写只有 P01 一张。"""),
    md("## 1. 参数与环境"),
    code("""import collections
import datetime
import hashlib
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
from pathlib import Path

PROJECT = Path(os.environ.get("MOSS_PROJECT", "data/moss01")).resolve()
SOURCE = PROJECT / "source"
SELECTION = SOURCE / "selection.json"
SELECTION_SHA256 = "dae6da2badc7dbeb57ded878a0c21587982f7b4b7544792951891c3abd474850"   # 人工导出版本
TRIGGER = "moss01"
REPEATS = 1
TRAIN_DIR = PROJECT / f"data/train/{REPEATS}_{TRIGGER}"
PREVIEW_DIR = PROJECT / "data/previews"
REPORT_DIR = PROJECT / "data/reports"

RUN_STARTED = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
for d in (PREVIEW_DIR, REPORT_DIR):
    d.mkdir(parents=True, exist_ok=True)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


print("project :", PROJECT)
print("host    :", socket.gethostname())
print("python  :", sys.version.split()[0], sys.executable)
print("started :", RUN_STARTED)"""),
    md("## 2. 读取并校验 selection.json"),
    code("""assert sha256(SELECTION) == SELECTION_SHA256, "selection.json 与记录的版本不一致"
sel = json.loads(SELECTION.read_text(encoding="utf-8"))
items = sel["items"]
assert sel["trigger"] == TRIGGER and sel["n"] == len(items)
ids = [it["id"] for it in items]
assert len(ids) == len(set(ids)), "镜头编号重复"
assert not set(ids) & set(sel["dropped"]), "同一镜头既选用又丢弃"
missing = [it["file"] for it in items if not (SOURCE / it["file"]).exists()]
assert not missing, missing
print(f"selected {len(items)} | dropped {len(sel['dropped'])}: {sel['dropped']}")
print("exported at", sel["exported"])"""),
    md("## 3. 源图检查"),
    code("""import pandas as pd
from PIL import Image

rows = []
for it in items:
    p = SOURCE / it["file"]
    with Image.open(p) as im:
        im.verify()
    with Image.open(p) as im:
        w, h, mode, fmt = im.width, im.height, im.mode, im.format
    f = it["fields"]
    rows.append({"id": it["id"], "batch": it["batch"], "file": it["file"], "format": fmt, "mode": mode,
                 "width": w, "height": h, "mp": round(w * h / 1e6, 2), "sha256": sha256(p),
                 "uniform": it["uniform"], **f, "caption": it["caption"]})
df = pd.DataFrame(rows)
print(df[["format", "mode"]].value_counts().to_dict())
print("sizes:", df.groupby(["width", "height"]).size().to_dict())
print("caption chars: min/median/max", df.caption.str.len().min(), int(df.caption.str.len().median()), df.caption.str.len().max())"""),
    md("## 4. 分布统计"),
    code("""def bucket_framing(s):
    return "full body" if "full" in s else "upper body" if "upper" in s else "close-up"


def bucket_angle(s):
    if s.startswith("back"):
        return "back"
    if s.startswith("side"):
        return "side profile " + ("left" if "left" in s else "right")
    if s.startswith("three"):
        return "3/4 " + ("left" if "left" in s else "right")
    return "front (high/low camera)" if "camera" in s else "front"


stats = {
    "batch": df.batch.value_counts().to_dict(),
    "framing": df.framing.map(bucket_framing).value_counts().to_dict(),
    "angle": df.angle.map(bucket_angle).value_counts().to_dict(),
    "uniform": {"uniform": int(df.uniform.sum()), "casual": int((~df.uniform).sum()),
                "uniform_share": round(float(df.uniform.mean()), 3)},
    "hair": df.hair.value_counts().head(8).to_dict(),
}
for k, v in stats.items():
    print(f"{k:8s}", v)"""),
    md("""## 5. 写入训练目录

kohya 风格：`data/train/1_moss01/<id>.png + <id>.txt`。文件名保留镜头编号便于追溯；**图片按字节原样复制**（PNG，不重新编码），KohakuMoss 训练时按长宽比分桶并缩放到约 1MP。"""),
    code("""assert TRAIN_DIR.resolve().is_relative_to((PROJECT / "data/train").resolve())
if TRAIN_DIR.parent.exists():
    shutil.rmtree(TRAIN_DIR.parent)
TRAIN_DIR.mkdir(parents=True)

manifest = []
for r in df.to_dict("records"):
    ext = Path(r["file"]).suffix.lower()
    shutil.copyfile(SOURCE / r["file"], TRAIN_DIR / f"{r['id']}{ext}")
    (TRAIN_DIR / f"{r['id']}.txt").write_text(r["caption"] + "\\n", encoding="utf-8")
    manifest.append({"id": r["id"], "image": f"{r['id']}{ext}", "caption_file": f"{r['id']}.txt",
                     "source": r["file"], "batch": r["batch"], "sha256": r["sha256"],
                     "size": [int(r["width"]), int(r["height"])], "uniform": bool(r["uniform"]),
                     "fields": {k: r[k] for k in ["framing", "angle", "expression", "hair", "outfit", "scene", "lighting"]},
                     "caption": r["caption"]})

with open(REPORT_DIR / "manifest.jsonl", "w", encoding="utf-8") as f:
    for m in manifest:
        f.write(json.dumps(m, ensure_ascii=False) + "\\n")
df.to_csv(REPORT_DIR / "selection_table.csv", index=False)
print(f"wrote {len(manifest)} pairs to {TRAIN_DIR}")"""),
    md("## 6. 完整性检查"),
    code("""checks = {}
imgs = sorted(p for p in TRAIN_DIR.iterdir() if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"})
txts = sorted(TRAIN_DIR.glob("*.txt"))
checks["count == selection n"] = len(imgs) == len(txts) == len(manifest) == sel["n"]
checks["every image has caption"] = {p.stem for p in imgs} == {p.stem for p in txts}
checks["caption starts with trigger"] = all(p.read_text(encoding="utf-8").startswith(TRIGGER + ", ") for p in txts)
checks["caption == selection caption"] = all(
    (TRAIN_DIR / m["caption_file"]).read_text(encoding="utf-8").strip() == m["caption"] for m in manifest)
checks["bytes identical to source"] = all(sha256(TRAIN_DIR / m["image"]) == m["sha256"] for m in manifest)
checks["no dropped shot used"] = not ({m["id"] for m in manifest} & set(sel["dropped"]))
checks["only image/txt in train dir"] = all(p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".txt"}
                                            for p in TRAIN_DIR.iterdir())

for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
assert all(checks.values()), 'integrity check failed'"""),
    md("## 7. 联系图"),
    code("""from PIL import ImageDraw, ImageFont

THUMB, COLS = 240, 8
rows_n = -(-len(manifest) // COLS)
sheet = Image.new("RGB", (COLS * THUMB, rows_n * (THUMB + 34)), "white")
draw = ImageDraw.Draw(sheet)
font = ImageFont.load_default(size=13)
for i, m in enumerate(manifest):
    with Image.open(TRAIN_DIR / m["image"]) as im:
        im = im.convert("RGB")
        im.thumbnail((THUMB, THUMB))
        x, y = (i % COLS) * THUMB, (i // COLS) * (THUMB + 34)
        sheet.paste(im, (x + (THUMB - im.width) // 2, y))
    draw.text((x + 3, y + THUMB + 2), f"{m['id']} {'uniform' if m['uniform'] else 'casual'}", fill="black", font=font)
    draw.text((x + 3, y + THUMB + 17), bucket_framing(m["fields"]["framing"]) + " / " + bucket_angle(m["fields"]["angle"]),
              fill="#555", font=font)
sheet.save(PREVIEW_DIR / "train_set.jpg", quality=86)
display(sheet.reduce(2))"""),
    md("## 8. 报告"),
    code("""def pip_versions(names):
    from importlib.metadata import version
    return {n: version(n) for n in names}


def gpu_info():
    try:
        return subprocess.run(["nvidia-smi", "--query-gpu=index,name,memory.total", "--format=csv,noheader"],
                              capture_output=True, text=True, timeout=20).stdout.strip().splitlines()
    except Exception as e:
        return [f"unavailable: {e}"]


(REPORT_DIR / "sha256sums.txt").write_text(
    "".join(f"{sha256(p)}  {p.name}\\n" for p in sorted(TRAIN_DIR.iterdir())))
run_info = {
    "started": RUN_STARTED,
    "finished": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
    "host": socket.gethostname(), "platform": platform.platform(),
    "python": sys.version, "packages": pip_versions(["pillow", "pandas"]), "gpus": gpu_info(),
    "source": {"generator": "Codex / gpt-image-2 with reference image ref_face_17.png",
               "selection_sha256": SELECTION_SHA256, "selection_exported": sel["exported"],
               "review": "Claude 看图预填（claude_suggestions.json），人工复核导出；与建议对比 0 处修改"},
    "trigger": TRIGGER, "repeats": REPEATS, "n": len(manifest), "dropped": sel["dropped"],
    "stats": stats, "checks": checks, "train_dir": str(TRAIN_DIR.relative_to(PROJECT)),
}
(REPORT_DIR / "run_info.json").write_text(json.dumps(run_info, ensure_ascii=False, indent=2))
print(json.dumps({k: run_info[k] for k in ("n", "stats", "train_dir")}, ensure_ascii=False, indent=2))"""),
]

nb = nbf.v4.new_notebook(cells=cells, metadata={
    "kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
    "language_info": {"name": "python"},
})
out = Path(sys.argv[1] if len(sys.argv) > 1 else "prepare_moss01_for_lora.ipynb")
nbf.write(nb, out)
print("wrote", out)
