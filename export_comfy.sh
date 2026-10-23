#!/usr/bin/env bash
# 把训练出的一个检查点导出成 ComfyUI 用的 LoRA，放进 ComfyUI/models/loras/。
#   bash export_comfy.sh 900                 # 第 900 步 → ComfyUI/models/loras/moss01.safetensors
#   bash export_comfy.sh 900 moss01_s900     # 自定义文件名
# 可选环境变量：RUN（训练输出目录，默认 data/moss01/runs/moss01-lora）、COMFY_DIR（默认 /root/ComfyUI）、
#               FUSED_QKV（默认 False；ComfyUI 原生会把分开的 q/k/v 映射到合并的 qkv 上，两种都能用）
set -euo pipefail
KIT="$(cd "$(dirname "$0")" && pwd)"
STEP="${1:?用法：bash export_comfy.sh <步数> [文件名]}"
NAME="${2:-moss01}"
RUN="${RUN:-$KIT/data/moss01/runs/moss01-lora}"
COMFY_DIR="${COMFY_DIR:-/root/ComfyUI}"
WEIGHTS="${MOSS_WEIGHTS:-$KIT/weights/MOSS-Image-Base}"
CKPT="$RUN/checkpoints/$(printf 'step_%08d' "$STEP")/trainable.safetensors"
[ -f "$CKPT" ] || { echo "找不到检查点：$CKPT"; ls "$RUN/checkpoints" 2>/dev/null; exit 1; }
OUT="$COMFY_DIR/models/loras/$NAME.safetensors"
mkdir -p "$(dirname "$OUT")"
source "$KIT/.venv/bin/activate"
cd "$KIT/vendor/kohakumoss-0.1.0"
PYTHONWARNINGS=ignore CUDA_VISIBLE_DEVICES= kogine run scripts/export/export.py \
    --set WEIGHTS="$WEIGHTS" --set ADAPTER="$CKPT" \
    --set FORMAT=comfy --set FUSED_QKV="${FUSED_QKV:-False}" --set OUT="$OUT" 2>&1 | grep -vE "distutils|addpackage"
echo "已导出：$OUT（$(du -h "$OUT" | cut -f1)）。在 ComfyUI 的 LoRA 加载节点里选 $NAME.safetensors"
