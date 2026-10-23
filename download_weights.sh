#!/usr/bin/env bash
# 不在优云智算上时：从 ModelScope 下载 Comfy-Org 打包的 bf16 权重（约 30GB），目录结构与 link_weights.sh 相同。
set -euo pipefail
KIT="$(cd "$(dirname "$0")" && pwd)"
DST="$KIT/weights/MOSS-Image-Base-bf16"
mkdir -p "$DST"
VIRTUAL_ENV="$KIT/.venv" uv pip install -q -i "${PIP_INDEX:-https://pypi.tuna.tsinghua.edu.cn/simple}" modelscope
"$KIT/.venv/bin/python" - "$DST" <<'PY'
import sys
from modelscope import snapshot_download
snapshot_download("Comfy-Org/MOSS-Image", local_dir=sys.argv[1], allow_patterns=[
    "diffusion_models/moss_image_base_bf16.safetensors",
    "text_encoders/qwen3.5_9b_bf16.safetensors",
    "vae/flux2-vae_small.safetensors"])
print("downloaded to", sys.argv[1])
PY
