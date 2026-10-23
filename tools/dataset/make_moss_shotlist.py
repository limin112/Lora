"""Generate a repeatable Moss LoRA shot list and prompt queue."""
import csv
from itertools import cycle

TRIGGER = "moss01"
CHARACTER = (
    "an original fictional British boarding-school girl, about 17 years old, "
    "pale cool porcelain skin, light icy-gray eyes, straight high nose bridge, "
    "softly rounded youthful cheeks, pale silver-blonde hair in neat braids, "
    "cool aristocratic heiress presence, age-appropriate proportions"
)

FRAMINGS = [
    ("close-up portrait", "head and shoulders", "1024x1024"),
    ("upper-body portrait", "waist up", "1024x1536"),
    ("full-body portrait", "head to toe, feet visible", "1024x1536"),
]
ANGLES = ["front view", "three-quarter view facing left", "three-quarter view facing right",
          "side profile facing left", "side profile facing right", "back view, looking over shoulder"]
EXPRESSIONS = [
    "level eye contact with a calm neutral expression",
    "looking down thoughtfully at an open book, relaxed posture",
    "soft side glance with a faintly amused expression",
    "quietly confident gaze at eye level, head held naturally",
    "small restrained smile, composed aristocratic manner",
    "slightly impatient expression while looking to the side",
    "gentle thoughtful gaze through a window",
    "subtle proud pout without raising the chin",
]
OUTFITS = [
    "dark emerald cardigan, white blouse, green ribbon tie, charcoal pleated skirt",
    "black school cloak with silver edging over the emerald uniform",
    "formal emerald velvet school dress with white collar and silver brooch",
    "winter uniform with a charcoal wool coat, emerald scarf, and polished loafers",
    "library study outfit with emerald knit vest, white blouse, and plaid skirt",
    "ceremonial school uniform with a black capelet and silver-trimmed green sash",
]
HAIRSTYLES = [
    "two neat French braids tied with dark green ribbons",
    "half-up braided crown with the rest falling over the shoulders",
    "low braided ponytail with a center part",
    "single side braid over the right shoulder",
    "neat low bun with two soft face-framing strands",
    "double Dutch braids with small silver hair pins",
]
EARRINGS = [
    "small silver stud earrings",
    "tiny emerald drop earrings",
    "simple pearl studs",
    "delicate silver hoop earrings",
    "small antique silver teardrop earrings",
    "no visible earrings",
]
SCENES = [
    ("plain cool-gray studio backdrop", "soft diffused studio light"),
    ("candlelit stone school corridor", "warm candlelight with cool fill"),
    ("old library with dark wooden shelves", "window light and green reflected light"),
    ("rainy school courtyard", "overcast daylight and wet reflections"),
    ("grand stair hall with gothic arches", "cool morning light"),
    ("quiet greenhouse with ivy and glass panes", "soft overcast daylight"),
    ("school dining hall prepared for dinner", "candlelight and muted green shadows"),
    ("snowy cloister walkway", "pale winter daylight"),
]

rows = []
for i in range(48):
    framing, detail, size = FRAMINGS[i % len(FRAMINGS)]
    angle = ANGLES[(i * 2) % len(ANGLES)]
    expression = EXPRESSIONS[(i * 3) % len(EXPRESSIONS)]
    outfit = OUTFITS[(i * 5) % len(OUTFITS)]
    hairstyle = HAIRSTYLES[(i * 2) % len(HAIRSTYLES)]
    earrings = EARRINGS[(i * 3) % len(EARRINGS)]
    scene, light = SCENES[(i * 3) % len(SCENES)]
    prompt = (
        f"Photorealistic cinematic costume-test image of {CHARACTER}. "
        f"{framing}, {detail}, {angle}, {expression}. Her hair is styled in {hairstyle}; she wears {earrings}. Wearing {outfit}. "
        f"Background: {scene}. Lighting: {light}. Keep the same person as the reference image. "
        "Natural skin texture, clean anatomy, consistent hair and eye color, sharp focus. "
        "No text, watermark, logo, or real-person likeness."
    )
    caption = ", ".join([TRIGGER, framing, detail, angle, expression, f"hairstyle: {hairstyle}", f"earrings: {earrings}", f"wearing {outfit}", scene, light])
    rows.append({"id": f"M{i+1:02d}", "size": size, "framing": framing, "detail": detail,
                 "angle": angle, "expression": expression, "outfit": outfit, "scene": scene,
                 "lighting": light, "prompt": prompt, "caption": caption})

with open("moss_shotlist.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)

with open("moss_prompts.txt", "w", encoding="utf-8") as f:
    for row in rows:
        f.write(f"[{row['id']}] size={row['size']}\n{row['prompt']}\n\n")

print(f"wrote {len(rows)} prompts to moss_shotlist.csv and moss_prompts.txt")
