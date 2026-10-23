#!/usr/bin/env bash
# moss01 人物 LoRA：生成训练配置 → 检查数据 → 文本/潜变量缓存 → 训练。
# 前提：setup_env.sh 已运行；权重已就位（link_weights.sh / download_weights.sh）；
#       训练集已生成（运行 prepare_moss01_for_lora.ipynb，得到 data/moss01/data/train/1_moss01/）。
# 可选环境变量：GPUS（默认 0，可写 "0,1,2" 多卡）；STEPS（默认按卡数折算成相同训练量）
set -euo pipefail
KIT="$(cd "$(dirname "$0")" && pwd)"
PROJECT="${MOSS_PROJECT:-$KIT/data/moss01}"
WEIGHTS="${MOSS_WEIGHTS:-$KIT/weights/MOSS-Image-Base-bf16}"
GPUS="${GPUS:-0}"
NGPU=$(echo "$GPUS" | tr ',' '\n' | grep -c .)
# 训练量：单卡 1200 步（每步 2 张图），多卡按卡数等比缩短；检查点和验证图间隔同比例
STEPS="${STEPS:-$((1200 / NGPU))}"
SAVE_EVERY=$((STEPS / 8)); SAMPLE_EVERY=$((STEPS / 4))
KM="$KIT/vendor/kohakumoss-0.1.0"
source "$KIT/.venv/bin/activate"
export PYTHONWARNINGS=ignore TMPDIR="$PROJECT/tmp" XDG_CACHE_HOME="$PROJECT/cache" \
       TORCHINDUCTOR_CACHE_DIR="$PROJECT/cache/torchinductor" TRITON_CACHE_DIR="$PROJECT/cache/triton"
mkdir -p "$TMPDIR" "$XDG_CACHE_HOME"
[ -d "$PROJECT/data/train/1_moss01" ] || { echo "训练集不存在：先运行 prepare_moss01_for_lora.ipynb"; exit 1; }
cd "$KM"
CFG=configs/user/moss01-lora
GPU_ARGS=(); [ "$NGPU" -gt 1 ] && GPU_ARGS=(--gpus "$NGPU")
CUDA_VISIBLE_DEVICES="$GPUS" kohakumoss-config new train --force --weights "$WEIGHTS" --data "$PROJECT/data/train" \
    --source kohya --name moss01-lora --steps "$STEPS" "${GPU_ARGS[@]}"
cat >> "$CFG.py" <<CONF

# ---- moss01 覆盖项（下面的值覆盖上面的 layer） ----
DATASETS = [{"source": "kohya", "path": "$PROJECT/data/train", "repeat_prefix": "first",
             "artist_from_folder": None, "txt_as": "tags", "include_root": False}]   # 触发词只来自 .txt
# 只固定触发词；其余短语（构图/角度/表情/发型/服装/场景/光线）打乱 + 10% 丢弃
CAPTION = {"template": "tags", "keep": [], "keep_first": 1, "shuffle": True, "tag_dropout": 0.1,
           "underscores": True, "unescape": True}
CAPTION_VARIANTS = 8
SEED = 42
SAVE_EVERY = $SAVE_EVERY
KEEP_LAST = 20
SAMPLE_EVERY = $SAMPLE_EVERY
SAMPLE_SEEDS = (0,)
SAMPLE_PROMPTS = [
    # 1 训练分布内
    "moss01, upper-body portrait, three-quarter view facing right, calm expression, two long braids hairstyle, wearing school uniform: dark green cardigan, white blouse, green ribbon tie, old library with wooden shelves, warm window light",
    # 2 便装：测服装绑定
    "moss01, upper-body portrait, front view, bright smile, long loose straight hair hairstyle, wearing a red knit sweater, cozy modern cafe interior, warm indoor light",
    # 3 全身
    "moss01, full-body portrait, front view, walking, long loose straight hair hairstyle, wearing a white summer dress and sandals, sunny beach, bright midday sun",
    # 4 左侧脸特写
    "moss01, close-up portrait, side profile facing left, calm expression, low bun hairstyle, wearing a gray turtleneck sweater, plain gray studio backdrop, soft studio light",
    # 5 泄漏检查：不带触发词
    "a young woman, upper-body portrait, front view, calm expression, long loose hair, wearing a navy blazer, modern office, soft daylight",
]
OUTPUT_DIR = "$PROJECT/runs"
CONF
kohakumoss-config check "$CFG.py"
cp "$CFG.py" "${CFG}_data.py" "$PROJECT/"            # 配置留档
FIRST_GPU="${GPUS%%,*}"
CUDA_VISIBLE_DEVICES="$FIRST_GPU" kogine run scripts/data/cache_text.py --config "${CFG}_data.py"
echo "[$(date -Is)] TEXT_CACHE_DONE"
CUDA_VISIBLE_DEVICES="$FIRST_GPU" kogine run scripts/data/cache_latents.py --config "${CFG}_data.py"
echo "[$(date -Is)] LATENT_CACHE_DONE"
CUDA_VISIBLE_DEVICES="$GPUS" kogine run scripts/train/moss.py --config "$CFG.py"
echo "[$(date -Is)] TRAIN_DONE"
