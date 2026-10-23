#!/usr/bin/env bash
# 下载 MOSS-Image-Base 权重（HF / diffusers 目录格式，约 27GB）到 weights/MOSS-Image-Base。
# 来源：ModelScope 上的 OpenMOSS/MOSS-Image-Base（与 Hugging Face 上的 OpenMOSS-Team/MOSS-Image-Base 相同）。
# 注意：KohakuMoss 0.1.0 的训练只支持这种目录格式（transformer/ text_encoder/ tokenizer/ vae/），
#       不支持 ComfyUI 打包的单文件格式。
set -euo pipefail
KIT="$(cd "$(dirname "$0")" && pwd)"
export PATH="$HOME/.local/bin:/usr/local/miniconda3/bin:$PATH"
DST="$KIT/weights/MOSS-Image-Base"
VIRTUAL_ENV="$KIT/.venv" uv pip install -q -i "${PIP_INDEX:-https://pypi.tuna.tsinghua.edu.cn/simple}" modelscope
"$KIT/.venv/bin/python" - "$DST" <<'PY'
import sys
from modelscope import snapshot_download
p = snapshot_download("OpenMOSS/MOSS-Image-Base", local_dir=sys.argv[1],
                      ignore_file_pattern=[r"assets/.*", r".*\.webp", r".*\.svg"], max_workers=8)
print("downloaded to", p)
PY
