"""Claude 看图后的预填建议 → claude_suggestions.json（挑选页面打开时作为默认值，人工可改）。"""
import json

U_CARD = "school uniform: dark green cardigan, white blouse, green ribbon tie"
U_CLOAK = "school uniform with a black embroidered cloak, white blouse, green ribbon tie"
U_VELVET = "dark green velvet school dress with silver trim and a green ribbon tie"
U_COAT = "school uniform with a charcoal wool coat and a green striped scarf"
U_VEST = "school uniform: white blouse, dark green vest, plaid pleated skirt, knee socks, loafers"
U_BLAZER = "school uniform: dark green blazer, pleated skirt, green ribbon tie"

SCENE = {  # 场景 → (场景描述, 光线)
    "studio": ("plain gray studio backdrop", "soft studio light"),
    "rain": ("rainy gothic courtyard", "overcast daylight"),
    "dining": ("candlelit dining hall", "warm candlelight"),
    "corridor": ("candlelit stone corridor", "warm candlelight"),
    "stair": ("gothic stair hall", "cool daylight"),
    "snow": ("snowy cloister walkway", "pale winter daylight"),
    "library": ("old library with wooden shelves", "warm window light"),
    "green": ("greenhouse with ivy", "soft daylight"),
    "window": ("stone corridor by a leaded window", "soft daylight"),
    "garden": ("garden courtyard with stone arches", "soft daylight"),
}
CU, UB, FB = "close-up portrait", "upper-body portrait", "full-body portrait"
F, L34, R34, LS, RS = ("front view", "three-quarter view facing left", "three-quarter view facing right",
                       "side profile facing left", "side profile facing right")
COOL = "cool calm expression, chin slightly raised"

# id: (用不用, 不用的原因, 构图, 角度, 表情/动作, 发型, 服装, 场景键)
M = {
    "M01": (False, "与 M25 几乎相同，留 M25", CU, F, COOL, "two long braids with green ribbons", U_CARD, "studio"),
    "M02": (True, "", UB, R34, COOL, "braided updo", U_CLOAK, "rain"),
    "M03": (True, "", FB, RS, "gazing out of a window", "low bun", U_VEST, "dining"),
    "M04": (True, "", UB, F, "looking down at an open book", "two long braids", U_COAT, "corridor"),
    "M05": (True, "", UB, R34, "faint smile, chin slightly raised", "half-up braided hair", U_VELVET, "stair"),
    "M06": (True, "", FB, R34, "calm expression", "low bun", U_CLOAK + ", knee socks, loafers", "snow"),
    "M07": (True, "", UB, F, COOL + ", sitting", "two long braids with green ribbons", U_CARD, "library"),
    "M08": (True, "", UB, F, "glancing to the side, chin slightly raised", "two long braids", U_CLOAK, "green"),
    "M09": (True, "", FB, R34, "calm expression, standing sideways", "low bun", U_VEST, "studio"),
    "M10": (True, "", CU, F, COOL, "two long braids", U_COAT, "rain"),
    "M11": (True, "", UB, R34, "looking to the side, chin resting on her hand, sitting", "single braid", U_VELVET, "dining"),
    "M12": (True, "", FB, R34, "reading a book while standing", "low bun", U_CLOAK + ", knee socks, loafers", "corridor"),
    "M13": (True, "", CU, F, COOL, "two long braids with green ribbons", U_CARD, "stair"),
    "M14": (True, "", UB, F, COOL, "single braid", U_CLOAK, "snow"),
    "M15": (True, "", FB, R34, "calm expression, looking at the viewer", "low bun", U_VEST, "library"),
    "M16": (True, "", CU, F, "glancing to the side, chin slightly raised", "two long braids", U_COAT, "green"),
    "M17": (True, "", UB, R34, COOL, "single side braid", U_VELVET, "studio"),
    "M18": (True, "", FB, RS, "looking into the distance", "low bun", "school uniform with a black hooded cloak, knee socks, loafers", "rain"),
    "M19": (True, "", UB, R34, "looking to the side", "two long braids", U_CARD, "dining"),
    "M20": (True, "", UB, F, "looking down at an open book", "single braid", U_CLOAK, "corridor"),
    "M21": (True, "", FB, R34, "calm expression", "low bun", U_VEST, "stair"),
    "M22": (True, "", CU, F, COOL, "two long braids", U_COAT, "snow"),
    "M23": (True, "", UB, F, COOL + ", sitting", "single braid", U_VELVET, "library"),
    "M24": (True, "", FB, R34, "looking to the side, arms folded", "low bun", U_CLOAK + ", knee socks, loafers", "green"),
    "M25": (True, "", CU, F, COOL, "two long braids with green ribbons", U_CARD, "studio"),
    "M26": (False, "与 M02 几乎相同", UB, R34, COOL, "braided updo", U_CLOAK, "rain"),
    "M27": (False, "与 M03 几乎相同", FB, RS, "gazing out of a window", "low bun", U_VEST, "dining"),
    "M28": (False, "与 M04 几乎相同", UB, F, "looking down at an open book", "two long braids", U_COAT, "corridor"),
    "M29": (False, "与 M05 几乎相同", UB, R34, COOL, "single braid", U_VELVET, "stair"),
    "M30": (False, "与 M06 几乎相同", FB, R34, "calm expression", "low bun", U_CLOAK, "snow"),
    "M31": (False, "与 M07 几乎相同", UB, F, COOL + ", sitting", "two long braids", U_CARD, "library"),
    "M32": (False, "与 M08 几乎相同", UB, F, "glancing to the side", "two long braids", U_CLOAK, "green"),
    "M33": (True, "", UB, F, COOL, "long loose straight hair", U_CLOAK, "corridor"),
    "M34": (False, "M33–M38 近重复（同一走廊同一姿势），且背景有学院旗帜", UB, F, COOL, "long loose wavy hair", U_CLOAK, "corridor"),
    "M35": (False, "M33–M38 近重复", UB, F, COOL, "low ponytail", U_CLOAK, "corridor"),
    "M36": (True, "", UB, F, COOL, "single side braid", U_CLOAK, "corridor"),
    "M37": (False, "M33–M38 近重复", UB, F, COOL, "long loose hair with a dark bow", U_CLOAK, "corridor"),
    "M38": (False, "M33–M38 近重复", UB, F, COOL, "loose low bun", U_CLOAK, "corridor"),
    "M39": (True, "", UB, R34, "calm expression", "low ponytail", "school uniform with a black hooded cloak, green ribbon tie", "rain"),
    "M40": (True, "", UB, R34, "looking down at white flowers", "long loose straight hair with a black headband", U_BLAZER, "green"),
    "M41": (True, "", UB, F, "chin resting on her hand, sitting", "long loose wavy hair", U_VELVET, "dining"),
    "M42": (True, "", UB, R34, "looking to the side", "hair tied back", U_COAT, "snow"),
    "M43": (True, "", UB, R34, "looking to the side", "long loose hair with a black bow", U_BLAZER, "stair"),
    "M44": (True, "", UB, F, COOL, "long loose straight hair", U_CLOAK, "studio"),
    "M45": (True, "", FB, F, "calm expression", "low bun", U_BLAZER + ", knee socks, loafers", "window"),
    "M46": (True, "", UB, F, "eyes lowered, reading a book, head resting on her hand, sitting", "two long braids", U_CLOAK, "library"),
    "M47": (True, "", UB, F, "faint smile", "long loose wavy half-up hair", U_CLOAK, "garden"),
    "M48": (True, "", UB, R34, "calm expression", "single side braid", U_CLOAK, "window"),
}

# 补拍：全部采用；字段沿用清单，只改看图后与清单不符的地方
P_OVERRIDES = {
    "P02": {"angle": R34, "note": "要求真侧脸，实际是 3/4 侧，按实际写"},
    "P03": {"angle": L34, "note": "要求侧脸，实际身体侧对、脸 3/4 侧"},
    "P04": {"angle": F, "note": "要求侧脸，实际接近正脸、低头看书"},
    "P09": {"expression": "soft smile", "note": "微笑比较淡"},
    "P12": {"expression": "annoyed pout, arms crossed, chin slightly raised", "note": "仍有点抬下巴"},
}

# 补拍的构图和校服说法统一成与第一批相同的词，服装绑定实验才可比
import csv
SHOT_UNIFORM = "dark emerald cardigan, white blouse, green ribbon tie, charcoal pleated skirt"
FRAMING_MAP = {"close-up portrait, head and shoulders": CU, "upper-body portrait, waist up": UB,
               "full-body portrait, head to toe, feet visible": FB}
for r in csv.DictReader(open("supplement/moss_supplement_shotlist.csv", encoding="utf-8")):
    o = P_OVERRIDES.setdefault(r["id"], {})
    o.setdefault("framing", FRAMING_MAP[r["framing"]])
    if SHOT_UNIFORM in r["outfit"]:
        o.setdefault("outfit", r["outfit"].replace(SHOT_UNIFORM, "school uniform: dark green cardigan, white blouse, "
                                                                  "green ribbon tie, charcoal pleated skirt"))

out = {}
for k, (use, reason, framing, angle, expr, hair, outfit, scene) in M.items():
    sc, light = SCENE[scene]
    out[k] = {"use": use, "note": ("不用：" + reason) if not use else "用",
              "fields": {"framing": framing, "angle": angle, "expression": expr, "hair": hair,
                         "outfit": outfit, "scene": sc, "lighting": light}}
for i in range(1, 21):
    pid = f"P{i:02d}"
    o = dict(P_OVERRIDES.get(pid, {}))
    note = o.pop("note", "")
    out[pid] = {"use": True, "note": "用" + ("；" + note if note else ""), "fields": o}

json.dump(out, open("claude_suggestions.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
keep = [k for k, v in out.items() if v["use"]]
print("use", len(keep), "drop", len(out) - len(keep), [k for k, v in out.items() if not v["use"]])
