"""Generate the ComfyUI workflow for the moss01 LoRA (UI format + API format).

python tools/build_comfy_workflow.py   ->  comfyui/moss01_lora_t2i.json      (drag into ComfyUI)
                                           comfyui/moss01_lora_t2i_api.json  (POST /prompt, used by comfy_smoke_test.py)

Settings follow the OpenMOSS USERGUIDE (50 steps, CFG 3, Euler, shift 5 = ComfyUI model default,
skip layer guidance on layer 22) and the Comfy-Org MOSS-Image Base template (SkipLayerGuidanceDiTSimple 0-50%).
"""
import json
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent.parent / "comfyui"

UNET = "moss_image_base_bf16.safetensors"
CLIP = "qwen3.5_9b_bf16.safetensors"
VAE = "flux2-vae.safetensors"
LORA = "moss01.safetensors"
POSITIVE = ("moss01, upper-body portrait, front view, bright smile, long loose straight hair hairstyle, "
            "wearing a yellow raincoat, rainy city street at night, neon reflections")
NEGATIVE = "nsfw, worst quality, bad anatomy, watermark, jpeg artifact"
NOTE = """## moss01 人物 LoRA

1. **LoRA**：`ComfyUI/models/loras/moss01.safetensors`（用 `export_comfy.sh` 从训练检查点导出）。强度 1.0；觉得太像训练图、衣服容易带出校服，可以降到 0.7–0.8。
2. **提示词**：`moss01` 放最前面，后面按训练时的写法：构图、角度、表情、发型、服装、场景、光线，用逗号分隔。
3. **采样**：50 步、CFG 3、Euler（OpenMOSS 官方推荐值）；shift 用模型默认的 5。Skip Layer Guidance 跳第 22 层，作用于前 50% 步数。
4. **模型**：Comfy-Org 打包的 MOSS-Image（bf16 DiT + Qwen3.5-9B + FLUX.2 VAE）。在优云智算上直接软链平台共享目录 `/model/ModelScope/Comfy-Org/MOSS-Image/`。
"""

# id, type, pos, size, widgets, inputs [(name, type, from_id, from_slot)], outputs [(name, type)]
NODES = [
    (1, "UNETLoader", [40, 80], [330, 82], [UNET, "default"], [], [("MODEL", "MODEL")]),
    (2, "LoraLoaderModelOnly", [400, 80], [330, 82], [LORA, 1.0], [("model", "MODEL", 1, 0)], [("MODEL", "MODEL")]),
    (3, "SkipLayerGuidanceDiTSimple", [760, 80], [300, 130], ["", "22", 0.0, 0.5],
     [("model", "MODEL", 2, 0)], [("MODEL", "MODEL")]),
    (4, "CLIPLoader", [40, 220], [330, 106], [CLIP, "moss_image", "default"], [], [("CLIP", "CLIP")]),
    (5, "CLIPTextEncode", [400, 220], [420, 200], [POSITIVE], [("clip", "CLIP", 4, 0)], [("CONDITIONING", "CONDITIONING")]),
    (6, "CLIPTextEncode", [400, 450], [420, 120], [NEGATIVE], [("clip", "CLIP", 4, 0)], [("CONDITIONING", "CONDITIONING")]),
    (7, "EmptyFlux2LatentImage", [40, 380], [330, 106], [1024, 1024, 1], [], [("LATENT", "LATENT")]),
    (8, "KSampler", [860, 250], [300, 262], [0, "fixed", 50, 3.0, "euler", "simple", 1.0],
     [("model", "MODEL", 3, 0), ("positive", "CONDITIONING", 5, 0), ("negative", "CONDITIONING", 6, 0),
      ("latent_image", "LATENT", 7, 0)], [("LATENT", "LATENT")]),
    (9, "VAELoader", [40, 520], [330, 58], [VAE], [], [("VAE", "VAE")]),
    (10, "VAEDecode", [1190, 250], [210, 46], [], [("samples", "LATENT", 8, 0), ("vae", "VAE", 9, 0)], [("IMAGE", "IMAGE")]),
    (11, "SaveImage", [1190, 340], [420, 460], ["moss01"], [("images", "IMAGE", 10, 0)], []),
    (12, "MarkdownNote", [40, 620], [780, 260], [NOTE], [], []),
]


def ui_workflow():
    links, out_links = [], {}
    for nid, _, _, _, _, inputs, _ in NODES:
        for slot, (_, typ, src, src_slot) in enumerate(inputs):
            lid = len(links) + 1
            links.append([lid, src, src_slot, nid, slot, typ])
            out_links.setdefault((src, src_slot), []).append(lid)
    nodes = []
    for order, (nid, typ, pos, size, widgets, inputs, outputs) in enumerate(NODES):
        in_links = {(nid, slot): l[0] for l in links for slot in range(len(inputs)) if l[3] == nid and l[4] == slot}
        nodes.append({
            "id": nid, "type": typ, "pos": pos, "size": size, "flags": {}, "order": order, "mode": 0,
            "inputs": [{"name": n, "type": t, "link": in_links[(nid, s)]} for s, (n, t, _, _) in enumerate(inputs)],
            "outputs": [{"name": n, "type": t, "links": out_links.get((nid, s), []), "slot_index": s}
                        for s, (n, t) in enumerate(outputs)],
            "properties": {"Node name for S&R": typ},
            "widgets_values": widgets,
        })
    return {"last_node_id": len(NODES), "last_link_id": len(links), "nodes": nodes, "links": links,
            "groups": [], "config": {}, "extra": {}, "version": 0.4}


def api_workflow():
    names = {
        "UNETLoader": ["unet_name", "weight_dtype"],
        "LoraLoaderModelOnly": ["lora_name", "strength_model"],
        "SkipLayerGuidanceDiTSimple": ["double_layers", "single_layers", "start_percent", "end_percent"],
        "CLIPLoader": ["clip_name", "type", "device"],
        "CLIPTextEncode": ["text"],
        "EmptyFlux2LatentImage": ["width", "height", "batch_size"],
        "KSampler": ["seed", None, "steps", "cfg", "sampler_name", "scheduler", "denoise"],
        "VAELoader": ["vae_name"],
        "VAEDecode": [],
        "SaveImage": ["filename_prefix"],
    }
    api = {}
    for nid, typ, _, _, widgets, inputs, _ in NODES:
        if typ not in names:
            continue
        args = {k: v for k, v in zip(names[typ], widgets) if k}
        args.update({n: [str(src), slot] for n, _, src, slot in inputs})
        api[str(nid)] = {"class_type": typ, "inputs": args}
    return api


OUT_DIR.mkdir(exist_ok=True)
(OUT_DIR / "moss01_lora_t2i.json").write_text(json.dumps(ui_workflow(), ensure_ascii=False, indent=1))
(OUT_DIR / "moss01_lora_t2i_api.json").write_text(json.dumps(api_workflow(), ensure_ascii=False, indent=1))
print("wrote", OUT_DIR / "moss01_lora_t2i.json", OUT_DIR / "moss01_lora_t2i_api.json")
