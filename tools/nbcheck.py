"""逐个单元格汇总一个已执行 Notebook 的结果：是否执行、是否报错、图片数、最后一行文本输出。"""
import json
import sys

nb = json.load(open(sys.argv[1], encoding="utf-8"))
for i, c in enumerate(nb["cells"]):
    if c["cell_type"] != "code":
        continue
    outs = c.get("outputs", [])
    errs = [o for o in outs if o.get("output_type") == "error"]
    imgs = sum(1 for o in outs if "image/png" in o.get("data", {}))
    txt = "".join("".join(o.get("text", "")) for o in outs if o.get("output_type") == "stream").strip()
    last = txt.splitlines()[-1][:140] if txt else ""
    first_line = "".join(c["source"]).splitlines()[0][:50]
    print(f"cell {i:2d} exec={c.get('execution_count')} err={len(errs)} imgs={imgs} | {first_line} | {last}")
    for e in errs:
        print("   ERROR:", e.get("ename"), str(e.get("evalue"))[:200])
