#!/usr/bin/env bash
# 在优云智算（UCloud Compshare）上使用平台共享模型目录里的 MOSS-Image，不用下载。
# 只链接 bf16 的 DiT、文本编码器和 FLUX.2 VAE（与 HF 版 OpenMOSS-Team/MOSS-Image-Base 是同一套权重）；
# 目录里只有这三个文件，KohakuMoss 就会默认使用它们（否则会默认挑 int8 量化版）。
set -euo pipefail
KIT="$(cd "$(dirname "$0")" && pwd)"
SRC="${MOSS_SHARED:-/model/ModelScope/Comfy-Org/MOSS-Image}"
DST="$KIT/weights/MOSS-Image-Base-bf16"
mkdir -p "$DST/diffusion_models" "$DST/text_encoders" "$DST/vae"
ln -sfn "$SRC/diffusion_models/moss_image_base_bf16.safetensors" "$DST/diffusion_models/"
ln -sfn "$SRC/text_encoders/qwen3.5_9b_bf16.safetensors" "$DST/text_encoders/"
ln -sfn "$SRC/vae/flux2-vae_small.safetensors" "$DST/vae/"
for f in "$DST"/*/*; do [ -e "$f" ] || { echo "missing: $f"; exit 1; }; done
echo "weights linked: $DST"
