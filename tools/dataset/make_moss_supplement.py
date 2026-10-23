"""Moss 补拍清单：针对第一批 48 张（M01–M48）的缺口逐个设计镜头，生成 CSV 和提示词。

缺口：没有真侧脸和背影；表情单一（总是抬下巴、略傲）；服装和场景只有校服和哥特校园；全身姿势单一。
每个镜头逐行写明，不用取模轮换（第一批的脚本里角度和发型被构图锁死了）。
"""
import csv

TRIGGER = "moss01"
# 与 make_moss_shotlist.py 保持一致（发色、眼睛、脸型是身份锚点，不改）
CHARACTER = (
    "an original fictional British boarding-school girl, about 17 years old, "
    "pale cool porcelain skin, light icy-gray eyes, straight high nose bridge, "
    "softly rounded youthful cheeks, pale silver-blonde hair, age-appropriate proportions"
)

UNIFORM = "dark emerald cardigan, white blouse, green ribbon tie, charcoal pleated skirt"

# (组, 构图, 尺寸, 角度/机位, 表情/动作, 发型, 服装, 场景, 光线, 验收要点)
SHOTS = [
    # A 真侧脸（左右各半）
    ("A_profile", "close-up portrait, head and shoulders", "1024x1024",
     "true 90-degree side profile facing left, only one eye visible, nose and chin silhouette clear",
     "calm neutral expression, chin level", "two neat French braids", UNIFORM,
     "plain cool-gray studio backdrop", "soft diffused studio light", "只看得到一只眼睛，鼻梁轮廓清楚"),
    ("A_profile", "close-up portrait, head and shoulders", "1024x1024",
     "true 90-degree side profile facing right, only one eye visible",
     "gentle closed-mouth smile, chin level", "long loose straight hair behind the ears", UNIFORM,
     "plain cool-gray studio backdrop", "soft diffused studio light", "朝右；只看得到一只眼睛"),
    ("A_profile", "upper-body portrait, waist up", "1024x1536",
     "side profile facing left, body turned sideways",
     "looking into the distance, relaxed", "low braided ponytail", "a cream cable-knit sweater and light blue jeans",
     "bright modern cafe by a window", "soft window light", "便装；身体和脸都是侧面"),
    ("A_profile", "upper-body portrait, waist up", "1024x1536",
     "side profile facing right",
     "reading a paperback book, eyes down", "single side braid over the left shoulder", UNIFORM,
     "old library with dark wooden shelves", "warm window light", "朝右；低头看书"),
    # B 背影 / 回头
    ("B_back", "upper-body portrait, waist up", "1024x1536",
     "seen from behind, head turned back over her right shoulder toward the camera",
     "soft surprised expression", "long loose straight hair", "a navy hoodie",
     "busy modern city street", "overcast daylight", "后背朝镜头，只回头"),
    ("B_back", "full-body portrait, head to toe, feet visible", "1024x1536",
     "back view, walking away from the camera, face not visible",
     "relaxed walking pose", "two neat French braids", UNIFORM + ", black tights, polished loafers",
     "snowy cloister walkway", "pale winter daylight", "完全背影，能看到鞋"),
    ("B_back", "full-body portrait, head to toe, feet visible", "1024x1536",
     "back three-quarter view, looking back over her left shoulder",
     "small friendly smile", "half-up hairstyle with a black ribbon",
     "a long camel wool coat, dark jeans, white sneakers",
     "autumn park path with fallen leaves", "golden hour sunlight", "背后 3/4，回头；便装"),
    # C 表情（平视、下巴不抬）
    ("C_expression", "close-up portrait, head and shoulders", "1024x1024",
     "front view, camera at eye level",
     "bright open-mouth laugh, eyes slightly squinted, chin level", "long loose straight hair",
     "a plain white t-shirt", "plain warm-gray studio backdrop", "soft diffused studio light", "真的在笑，露牙"),
    ("C_expression", "close-up portrait, head and shoulders", "1024x1024",
     "three-quarter view facing left, camera at eye level",
     "warm genuine smile, chin level", "two neat French braids", UNIFORM,
     "plain cool-gray studio backdrop", "soft diffused studio light", "微笑，不是傲气的表情"),
    ("C_expression", "close-up portrait, head and shoulders", "1024x1024",
     "front view, camera slightly above eye level, she looks up at the camera",
     "curious wide-eyed expression", "low bun with face-framing strands", "a light gray sweater",
     "plain cool-gray studio backdrop", "soft diffused studio light", "俯拍，她抬眼看镜头"),
    ("C_expression", "upper-body portrait, waist up", "1024x1536",
     "three-quarter view facing right",
     "eyes closed, peaceful relaxed smile, face tilted slightly down", "long loose straight hair",
     "a pale yellow cotton blouse", "sunny garden with flowers", "warm afternoon sunlight", "闭眼，低头"),
    ("C_expression", "close-up portrait, head and shoulders", "1024x1024",
     "front view, camera at eye level",
     "pouting with mild annoyance, arms crossed", "two Dutch braids", UNIFORM,
     "rainy school courtyard", "overcast daylight", "不开心/嘟嘴，下巴不抬"),
    # D 机位
    ("D_camera", "full-body portrait, head to toe, feet visible", "1024x1536",
     "high angle shot from above, she looks up at the camera",
     "friendly smile", "single side braid", "a denim jacket over a white t-shirt, black jeans, white sneakers",
     "city plaza with stone tiles", "midday sun", "俯拍全身"),
    ("D_camera", "upper-body portrait, waist up", "1024x1536",
     "front view, camera at eye level, head slightly tilted to one side",
     "relaxed neutral expression, chin level", "long loose straight hair", UNIFORM,
     "grand stair hall with arches", "cool morning light", "平视，头微微歪"),
    # E 便装和现代场景（服装不能总是校服）
    ("E_casual", "full-body portrait, head to toe, feet visible", "1024x1536",
     "three-quarter view facing left",
     "jogging, mid-stride, cheerful expression", "high ponytail",
     "a gray zip-up sports jacket, black running leggings, running shoes",
     "riverside running path", "early morning light", "运动装；在跑步"),
    ("E_casual", "full-body portrait, head to toe, feet visible", "1024x1536",
     "front view",
     "standing and holding a paper coffee cup, small smile", "long loose straight hair",
     "a knee-length navy summer dress with short sleeves, white sneakers",
     "sunny modern shopping street", "bright daylight", "得体的连衣裙；现代街道"),
    ("E_casual", "upper-body portrait, waist up", "1024x1536",
     "three-quarter view facing right",
     "laughing while talking, natural candid moment", "low bun",
     "an oversized beige knit sweater", "cozy modern cafe interior", "warm indoor light", "现代咖啡馆"),
    ("E_casual", "full-body portrait, head to toe, feet visible", "1024x1536",
     "front view, slightly low camera angle",
     "walking toward the camera, relaxed", "two neat French braids",
     "a red puffer jacket, dark jeans, winter boots", "snowy modern city street at night",
     "street lights and shop window glow", "冬装；夜景"),
    # F 全身姿势
    ("F_pose", "full-body portrait, head to toe, feet visible", "1024x1536",
     "three-quarter view facing right",
     "sitting on stone steps, elbows on knees, thoughtful", "long loose straight hair",
     UNIFORM + ", black tights, polished loafers", "old stone staircase outdoors", "soft overcast daylight", "坐姿，全身入镜"),
    ("F_pose", "full-body portrait, head to toe, feet visible", "1024x1536",
     "side profile facing right",
     "leaning against a brick wall, looking down at a phone", "half-up hairstyle with a black ribbon",
     "a white hoodie, light jeans, canvas sneakers", "quiet city alley", "late afternoon light", "侧身靠墙，看手机"),
]

rows = []
for i, (group, framing, size, angle, expr, hair, outfit, scene, light, check) in enumerate(SHOTS, start=1):
    prompt = (
        f"Photorealistic photo of {CHARACTER}. Keep exactly the same person as the reference image "
        f"(same face shape, icy-gray eyes, pale silver-blonde hair color). "
        f"{framing}, {angle}. Expression and action: {expr}. Hairstyle: {hair}. Wearing {outfit}. "
        f"Background: {scene}. Lighting: {light}. "
        "Modest, age-appropriate clothing. Natural skin texture, clean anatomy and hands, sharp focus. "
        "No text, watermark, logo, crest or house emblem, and no real-person likeness."
    )
    caption = ", ".join([TRIGGER, framing, angle, expr, f"{hair} hairstyle", f"wearing {outfit}", scene, light])
    rows.append({"id": f"P{i:02d}", "group": group, "size": size, "framing": framing, "angle": angle,
                 "expression": expr, "hair": hair, "outfit": outfit, "scene": scene, "lighting": light,
                 "check": check, "prompt": prompt, "caption_draft": caption})

with open("moss_supplement_shotlist.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
with open("moss_supplement_prompts.txt", "w", encoding="utf-8") as f:
    for r in rows:
        f.write(f"[{r['id']}] {r['group']} size={r['size']}  验收：{r['check']}\n{r['prompt']}\n\n")

from collections import Counter
print(len(rows), "shots")
for k in ["group", "framing", "size"]:
    print(k, dict(Counter(r[k] for r in rows)))
print("non-uniform outfits:", sum(UNIFORM not in r["outfit"] for r in rows))
