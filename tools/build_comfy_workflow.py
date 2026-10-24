"""Generate the ComfyUI workflows for the moss01 LoRA (UI format + API format).

python tools/build_comfy_workflow.py   ->  comfyui/moss01_lora_t2i.json          单张出图（拖进 ComfyUI）
                                           comfyui/moss01_lora_t2i_api.json      同上，API 格式（comfy_smoke_test.py 用）
                                           comfyui/moss01_leak_compare.json      对比：原模型 / 加 LoRA 不写 moss01 / 加 LoRA 写 moss01
                                           comfyui/moss01_leak_compare_api.json  同上，API 格式

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
NEUTRAL = ("A dreamy, luminous half-body fashion photograph of a beautiful 26-year-old adult East Asian woman standing among "
           "pale pink blossoms inside a glass greenhouse. She has expressive, slightly wide-set eyes, a delicate oval face, "
           "and chestnut hair loosely gathered into a bun. She has a full, natural bust, a softly defined waist and balanced "
           "hips. She wears an opaque pale rose off-the-shoulder dress; the softly ruffled neckline sits below both shoulders, "
           "revealing her collarbones and a tasteful hint of cleavage. The fitted, structured bodice follows her bust with "
           "realistic support and fabric folds, then gently narrows at the waist. Her body is turned slightly to the side "
           "while her face turns toward the close camera with a gentle, quietly alluring smile. One hand lightly touches a "
           "low flowering branch beside her shoulder; the other hangs relaxed at her side. The frame includes her full head, "
           "bare shoulders, bust, waist, hips and the skirt down to mid-thigh. Low sunlight rims loose strands of hair, a "
           "blurred blossom covers one corner of the frame, and a faint rainbow sheen touches the opposite edge. Pearly soft "
           "pastel light and gentle lens diffusion create a soft, romantic mood while keeping her eyes and body contours sharp.")
NEGATIVE = "nsfw, worst quality, bad anatomy, watermark, jpeg artifact"
SLG = ["", "22", 0.0, 0.5]
KSAMPLER = [0, "fixed", 50, 3.0, "euler", "simple", 1.0]

T2I_NOTE = """## moss01 人物 LoRA

1. **LoRA**：`ComfyUI/models/loras/moss01.safetensors`（用 `export_comfy.sh` 从训练检查点导出）。强度 1.0；觉得太像训练图、衣服容易带出校服，可以降到 0.7–0.8。
2. **提示词**：`moss01` 放最前面，后面按训练时的写法：构图、角度、表情、发型、服装、场景、光线，用逗号分隔。
3. **采样**：50 步、CFG 3、Euler（OpenMOSS 官方推荐值）；shift 用模型默认的 5。Skip Layer Guidance 跳第 22 层，作用于前 50% 步数。
4. **模型**：Comfy-Org 打包的 MOSS-Image（bf16 DiT + Qwen3.5-9B + FLUX.2 VAE）。在优云智算上直接软链平台共享目录 `/model/ModelScope/Comfy-Org/MOSS-Image/`。
"""

COMPARE_NOTE = """## 泄漏检查：这个 LoRA 到底学到了什么

只改左上角的**提示词**（不要写 moss01），点「运行」，同一个种子一次出三张：

- **A 原模型**：不加 LoRA，提示词原样；
- **B 加 LoRA，不写 moss01**：理想情况应该和 A 一样；
- **C 加 LoRA，写 moss01**：自动在提示词最前面加上 `moss01, `，应该是 Moss。

B 越像 C、越不像 A，泄漏越严重。可以换 LoRA 文件（moss01_s300 / s600 / moss01 / s1200）和强度对比。
本项目用最简单的方法训练（只有 Moss 的图，没有正则图），实测 B 和 C 几乎一样：提示词里没写的长相、人种、年龄感都会被拉向 Moss。
"""


def node(nid, typ, pos, size, widgets, inputs=(), outputs=(), title=None):
    """inputs: (name, type, src_id, src_slot, is_widget)  outputs: (name, type)"""
    return {"id": nid, "type": typ, "pos": pos, "size": size, "widgets": widgets,
            "inputs": [i if len(i) == 5 else (*i, False) for i in inputs], "outputs": list(outputs), "title": title}


def ui_workflow(nodes):
    links, out_links = [], {}
    for n in nodes:
        for slot, (_, typ, src, src_slot, _) in enumerate(n["inputs"]):
            lid = len(links) + 1
            links.append([lid, src, src_slot, n["id"], slot, typ])
            out_links.setdefault((src, src_slot), []).append(lid)
    ui_nodes = []
    for order, n in enumerate(nodes):
        ins = []
        for slot, (name, typ, _, _, is_widget) in enumerate(n["inputs"]):
            link = next(l[0] for l in links if l[3] == n["id"] and l[4] == slot)
            ins.append({"name": name, "type": typ, "link": link, **({"widget": {"name": name}} if is_widget else {})})
        d = {"id": n["id"], "type": n["type"], "pos": n["pos"], "size": n["size"], "flags": {}, "order": order,
             "mode": 0, "inputs": ins,
             "outputs": [{"name": nm, "type": t, "links": out_links.get((n["id"], s), []), "slot_index": s}
                         for s, (nm, t) in enumerate(n["outputs"])],
             "properties": {"Node name for S&R": n["type"]}, "widgets_values": n["widgets"]}
        if n["title"]:
            d["title"] = n["title"]
        ui_nodes.append(d)
    return {"last_node_id": max(n["id"] for n in nodes), "last_link_id": len(links), "nodes": ui_nodes,
            "links": links, "groups": [], "config": {}, "extra": {}, "version": 0.4}


WIDGET_NAMES = {
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
    "PrimitiveStringMultiline": ["value"],
    "StringConcatenate": ["string_a", "string_b", "delimiter"],
    "PrimitiveInt": ["value", None],
}


def api_workflow(nodes):
    api = {}
    for n in nodes:
        if n["type"] not in WIDGET_NAMES:
            continue
        args = {k: v for k, v in zip(WIDGET_NAMES[n["type"]], n["widgets"]) if k}
        args.update({name: [str(src), slot] for name, _, src, slot, _ in n["inputs"]})
        api[str(n["id"])] = {"class_type": n["type"], "inputs": args}
    return api


M, C, CO, L, V, I = ("MODEL", "MODEL"), ("CLIP", "CLIP"), ("CONDITIONING", "CONDITIONING"), \
    ("LATENT", "LATENT"), ("VAE", "VAE"), ("IMAGE", "IMAGE")

T2I = [
    node(1, "UNETLoader", [40, 80], [330, 82], [UNET, "default"], outputs=[M]),
    node(2, "LoraLoaderModelOnly", [400, 80], [330, 82], [LORA, 1.0], [("model", "MODEL", 1, 0)], [M]),
    node(3, "SkipLayerGuidanceDiTSimple", [760, 80], [300, 130], SLG, [("model", "MODEL", 2, 0)], [M]),
    node(4, "CLIPLoader", [40, 220], [330, 106], [CLIP, "moss_image", "default"], outputs=[C]),
    node(5, "CLIPTextEncode", [400, 220], [420, 200], [POSITIVE], [("clip", "CLIP", 4, 0)], [CO]),
    node(6, "CLIPTextEncode", [400, 450], [420, 120], [NEGATIVE], [("clip", "CLIP", 4, 0)], [CO]),
    node(7, "EmptyFlux2LatentImage", [40, 380], [330, 106], [1024, 1024, 1], outputs=[L]),
    node(8, "KSampler", [860, 250], [300, 262], KSAMPLER,
         [("model", "MODEL", 3, 0), ("positive", "CONDITIONING", 5, 0), ("negative", "CONDITIONING", 6, 0),
          ("latent_image", "LATENT", 7, 0)], [L]),
    node(9, "VAELoader", [40, 520], [330, 58], [VAE], outputs=[V]),
    node(10, "VAEDecode", [1190, 250], [210, 46], [], [("samples", "LATENT", 8, 0), ("vae", "VAE", 9, 0)], [I]),
    node(11, "SaveImage", [1190, 340], [420, 460], ["moss01"], [("images", "IMAGE", 10, 0)]),
    node(12, "MarkdownNote", [40, 620], [780, 260], [T2I_NOTE]),
]

# 对比：同一个种子、同一段提示词，三路采样
COL = [1240, 1620, 2000]
COMPARE = [
    node(1, "PrimitiveStringMultiline", [40, 40], [420, 200], [NEUTRAL], outputs=[("STRING", "STRING")],
         title="提示词（不要写 moss01）"),
    node(2, "PrimitiveStringMultiline", [40, 290], [300, 100], ["moss01"], outputs=[("STRING", "STRING")],
         title="触发词"),
    node(3, "StringConcatenate", [500, 290], [300, 150], ["", "", ", "],
         [("string_a", "STRING", 2, 0, True), ("string_b", "STRING", 1, 0, True)], [("STRING", "STRING")],
         title="触发词 + 提示词"),
    node(4, "PrimitiveInt", [40, 440], [300, 90], [0, "fixed"], outputs=[("INT", "INT")], title="种子（三张共用）"),
    node(5, "UNETLoader", [40, 590], [330, 90], [UNET, "default"], outputs=[M]),
    node(6, "LoraLoaderModelOnly", [420, 590], [330, 90], [LORA, 1.0], [("model", "MODEL", 5, 0)], [M]),
    node(7, "SkipLayerGuidanceDiTSimple", [860, 420], [300, 150], SLG, [("model", "MODEL", 5, 0)], [M],
         title="SLG（原模型）"),
    node(8, "SkipLayerGuidanceDiTSimple", [860, 620], [300, 150], SLG, [("model", "MODEL", 6, 0)], [M],
         title="SLG（加 LoRA）"),
    node(9, "CLIPLoader", [40, 730], [330, 110], [CLIP, "moss_image", "default"], outputs=[C]),
    node(10, "CLIPTextEncode", [860, 40], [300, 110], [""], [("clip", "CLIP", 9, 0), ("text", "STRING", 1, 0, True)],
         [CO], title="编码：提示词"),
    node(11, "CLIPTextEncode", [860, 210], [300, 110], [""], [("clip", "CLIP", 9, 0), ("text", "STRING", 3, 0, True)],
         [CO], title="编码：moss01 + 提示词"),
    node(12, "CLIPTextEncode", [420, 730], [400, 150], [NEGATIVE], [("clip", "CLIP", 9, 0)], [CO], title="负面提示词"),
    node(13, "EmptyFlux2LatentImage", [40, 900], [330, 120], [896, 1152, 1], outputs=[L]),
    node(14, "VAELoader", [40, 1070], [330, 70], [VAE], outputs=[V]),
]
for k, (title, model_src, pos_src, prefix) in enumerate([
        ("A 原模型", 7, 10, "compare/A_base"),
        ("B 加 LoRA，不写 moss01", 8, 10, "compare/B_lora_no_trigger"),
        ("C 加 LoRA，写 moss01", 8, 11, "compare/C_lora_trigger")]):
    ks, dec, save = 20 + k * 3, 21 + k * 3, 22 + k * 3
    COMPARE += [
        node(ks, "KSampler", [COL[k], 40], [340, 330], KSAMPLER,
             [("model", "MODEL", model_src, 0), ("positive", "CONDITIONING", pos_src, 0),
              ("negative", "CONDITIONING", 12, 0), ("latent_image", "LATENT", 13, 0), ("seed", "INT", 4, 0, True)],
             [L], title=f"{title}：采样"),
        node(dec, "VAEDecode", [COL[k], 420], [340, 50], [], [("samples", "LATENT", ks, 0), ("vae", "VAE", 14, 0)], [I]),
        node(save, "SaveImage", [COL[k], 520], [340, 430], [prefix], [("images", "IMAGE", dec, 0)], title=title),
    ]
COMPARE.append(node(40, "MarkdownNote", [1240, 1000], [1100, 240], [COMPARE_NOTE]))

OUT_DIR.mkdir(exist_ok=True)
for name, nodes in [("moss01_lora_t2i", T2I), ("moss01_leak_compare", COMPARE)]:
    (OUT_DIR / f"{name}.json").write_text(json.dumps(ui_workflow(nodes), ensure_ascii=False, indent=1))
    print("wrote", OUT_DIR / f"{name}.json")
for name, nodes in [("moss01_lora_t2i", T2I), ("moss01_leak_compare", COMPARE)]:
    (OUT_DIR / f"{name}_api.json").write_text(json.dumps(api_workflow(nodes), ensure_ascii=False, indent=1))
    print("wrote", OUT_DIR / f"{name}_api.json")
