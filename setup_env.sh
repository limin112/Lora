#!/usr/bin/env bash
# 安装 MOSS-Image LoRA 训练环境：KohakuMoss 0.1.0（PyPI 源码包，自带 configs/ scripts/）+ torch + Jupyter。
# 用法：bash setup_env.sh            （在工具包根目录运行）
# 可选环境变量：TORCH_CUDA=cu130|cu128|cu126（按驱动选，默认 cu130）；PIP_INDEX（默认清华源）
set -euo pipefail
KIT="$(cd "$(dirname "$0")" && pwd)"
cd "$KIT"
TORCH_CUDA="${TORCH_CUDA:-cu130}"
PIP_INDEX="${PIP_INDEX:-https://pypi.tuna.tsinghua.edu.cn/simple}"
TORCH_INDEX="https://download.pytorch.org/whl/${TORCH_CUDA}"

# 安装 uv：优先用已有的 pip（系统 python 或平台自带的 miniconda），都没有再用 apt
if ! command -v uv >/dev/null; then
  PIP=""
  for c in "python3 -m pip" "/usr/local/miniconda3/bin/pip" "pip3" "pip"; do
    if $c --version >/dev/null 2>&1; then PIP="$c"; break; fi
  done
  if [ -z "$PIP" ]; then
    apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq python3-pip >/dev/null
    PIP="python3 -m pip"
  fi
  $PIP install -q -i "$PIP_INDEX" uv
fi
export PATH="$HOME/.local/bin:/usr/local/miniconda3/bin:$PATH"
command -v uv >/dev/null || { echo "uv 安装失败"; exit 1; }
export UV_HTTP_TIMEOUT=300 UV_LINK_MODE=copy

# Python 3.12（与开发环境一致）。uv 默认从 GitHub 下载 Python，国内用 npmmirror 镜像
export UV_PYTHON_INSTALL_MIRROR="${UV_PYTHON_INSTALL_MIRROR:-https://registry.npmmirror.com/-/binary/python-build-standalone}"
[ -d .venv ] || uv venv -q -p 3.12 .venv
export VIRTUAL_ENV="$KIT/.venv"
uv pip install -q "torch>=2.13,<2.15" torchvision --index-url "$TORCH_INDEX"

mkdir -p vendor
if [ ! -d vendor/kohakumoss-0.1.0 ]; then
  .venv/bin/python -m pip --version >/dev/null 2>&1 || uv pip install -q -i "$PIP_INDEX" pip
  .venv/bin/python -m pip download -q -i "$PIP_INDEX" --no-deps --no-binary kohakumoss kohakumoss==0.1.0 -d vendor
  tar xzf vendor/kohakumoss-0.1.0.tar.gz -C vendor
fi
uv pip install -q -e "vendor/kohakumoss-0.1.0[cuda]" "torch>=2.13,<2.15" \
  --index-url "$PIP_INDEX" --extra-index-url "$TORCH_INDEX" --index-strategy unsafe-best-match
uv pip install -q -i "$PIP_INDEX" jupyterlab ipykernel nbconvert nbformat matplotlib pandas pillow
.venv/bin/python -m ipykernel install --user --name moss-train --display-name "Python (moss-train: KohakuMoss + torch)" >/dev/null

.venv/bin/python - <<'PY'
import torch, kohakumoss
print("torch", torch.__version__, "cuda", torch.version.cuda, "gpu", torch.cuda.is_available(),
      torch.cuda.get_device_name(0) if torch.cuda.is_available() else "-")
PY
echo SETUP_DONE
