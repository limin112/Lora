"""两端对齐的紧凑拼图：每行图片保持原比例、同一高度、正好铺满整行，几乎没有留白。"""
import json
import sys
from pathlib import Path

from PIL import Image


def collage(paths, out, width=2400, row_h=300, gap=6):
    ims = [Image.open(p).convert("RGB") for p in paths]
    rows, row, row_w = [], [], 0.0
    for im in ims:
        w = im.width * row_h / im.height
        row.append(im)
        row_w += w + gap
        if row_w - gap >= width:
            rows.append(row)
            row, row_w = [], 0.0
    if row:
        rows.append(row)
    placed = []
    y = 0
    for r in rows:
        ratio_sum = sum(im.width / im.height for im in r)
        full = (width - gap * (len(r) - 1)) / ratio_sum
        h = min(full, row_h * 1.15) if r is rows[-1] else full   # 最后一行不强行拉满
        x = 0
        for im in r:
            w = round(im.width / im.height * h)
            placed.append((im.resize((w, round(h))), x, y))
            x += w + gap
        y += round(h) + gap
    canvas = Image.new("RGB", (width, y - gap), "white")
    for im, x, yy in placed:
        canvas.paste(im, (x, yy))
    canvas.save(out, quality=88)
    print(out, canvas.size, len(ims), "images")


if __name__ == "__main__":
    vp = Path("/Users/limin/vsproject/tmp/moss/virtual_person")
    art = Path("/Users/limin/vsproject/tmp/moss/article/images")
    collage(sorted(vp.glob("M*.png"))[:24], art / "moss01_batch1_sample.jpg", row_h=320)
    collage(sorted((vp / "supplement/generated_gpt_image2").glob("p*.png")), art / "moss01_supplement.jpg", row_h=320)
    sel = json.load(open(vp / "selection.json", encoding="utf-8"))
    collage([vp / it["file"] for it in sel["items"]], art / "moss01_train_set.jpg", row_h=240)
