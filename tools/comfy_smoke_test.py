"""Queue the moss01 API workflow on a running ComfyUI and save the results (standard library only).

python tools/comfy_smoke_test.py --lora moss01.safetensors --out /tmp/comfy_test
    [--url http://127.0.0.1:8188] [--strength 1.0] [--seed 0] [--steps 50] [--prompt "..."]...
Without --prompt it runs the five fixed test prompts used during training.
"""
import argparse
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

PROMPTS = [
    "moss01, upper-body portrait, three-quarter view facing right, calm expression, two long braids hairstyle, wearing school uniform: dark green cardigan, white blouse, green ribbon tie, old library with wooden shelves, warm window light",
    "moss01, upper-body portrait, front view, bright smile, long loose straight hair hairstyle, wearing a red knit sweater, cozy modern cafe interior, warm indoor light",
    "moss01, full-body portrait, front view, walking, long loose straight hair hairstyle, wearing a white summer dress and sandals, sunny beach, bright midday sun",
    "moss01, close-up portrait, side profile facing left, calm expression, low bun hairstyle, wearing a gray turtleneck sweater, plain gray studio backdrop, soft studio light",
    "a young woman, upper-body portrait, front view, calm expression, long loose hair, wearing a navy blazer, modern office, soft daylight",
]

ap = argparse.ArgumentParser()
ap.add_argument("--url", default="http://127.0.0.1:8188")
ap.add_argument("--workflow", default=str(Path(__file__).resolve().parent.parent / "comfyui/moss01_lora_t2i_api.json"))
ap.add_argument("--lora", default="moss01.safetensors")
ap.add_argument("--strength", type=float, default=1.0)
ap.add_argument("--seed", type=int, default=0)
ap.add_argument("--steps", type=int, default=50)
ap.add_argument("--prompt", action="append")
ap.add_argument("--out", required=True)
ap.add_argument("--timeout", type=int, default=1800)
args = ap.parse_args()
out = Path(args.out)
out.mkdir(parents=True, exist_ok=True)


def call(path, data=None):
    req = urllib.request.Request(args.url + path, data=json.dumps(data).encode() if data is not None else None,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


base = json.loads(Path(args.workflow).read_text())
results = []
for i, prompt in enumerate(args.prompt or PROMPTS):
    wf = json.loads(json.dumps(base))
    for node in wf.values():
        ins = node["inputs"]
        if node["class_type"] == "LoraLoaderModelOnly":
            ins["lora_name"], ins["strength_model"] = args.lora, args.strength
        elif node["class_type"] == "KSampler":
            ins["seed"], ins["steps"] = args.seed, args.steps
        elif node["class_type"] == "SaveImage":
            ins["filename_prefix"] = f"smoke/{Path(args.lora).stem}_{i}"
    wf["5"]["inputs"]["text"] = prompt
    t0 = time.time()
    pid = json.loads(call("/prompt", {"prompt": wf}))["prompt_id"]
    while True:
        hist = json.loads(call(f"/history/{pid}"))
        if pid in hist:
            break
        if time.time() - t0 > args.timeout:
            raise SystemExit(f"timeout waiting for prompt {i}")
        time.sleep(3)
    status = hist[pid]["status"]
    if status.get("status_str") != "success":
        raise SystemExit(f"prompt {i} failed: {json.dumps(status)[:2000]}")
    for node_out in hist[pid]["outputs"].values():
        for img in node_out.get("images", []):
            q = urllib.parse.urlencode({"filename": img["filename"], "subfolder": img["subfolder"], "type": img["type"]})
            dst = out / f"{i}_{img['filename'].split('/')[-1]}"
            dst.write_bytes(call(f"/view?{q}"))
            results.append({"i": i, "prompt": prompt, "file": str(dst), "seconds": round(time.time() - t0, 1)})
            print(f"[{i}] {time.time() - t0:.0f}s -> {dst}", flush=True)
(out / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=1))
print("COMFY_SMOKE_OK", len(results))
