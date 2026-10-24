#!/usr/bin/env bash
# 安装 MOSS-Image LoRA 训练环境：KohakuMoss 0.1.0（PyPI 源码包，自带 configs/ scripts/）+ torch + Jupyter。
# 用法：bash setup_env.sh            （在工具包根目录运行）
# 可选环境变量：TORCH_CUDA=cu130|cu128|cu126（按驱动选，默认 cu130）；PIP_INDEX（默认清华源）
#               TORCH_SOURCE=aliyun（默认，torch 从阿里云镜像下载）| pytorch（PyTorch 官方源，海外用）
set -euo pipefail
KIT="$(cd "$(dirname "$0")" && pwd)"
cd "$KIT"
TORCH_CUDA="${TORCH_CUDA:-cu130}"
PIP_INDEX="${PIP_INDEX:-https://pypi.tuna.tsinghua.edu.cn/simple}"
TORCH_INDEX="https://download.pytorch.org/whl/${TORCH_CUDA}"
TORCH_SOURCE="${TORCH_SOURCE:-aliyun}"
TORCH_VERSION="${TORCH_VERSION:-2.14.1}"
TORCHVISION_VERSION="${TORCHVISION_VERSION:-0.29.1}"

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
export UV_HTTP_TIMEOUT=120 UV_LINK_MODE=copy UV_CONCURRENT_DOWNLOADS="${UV_CONCURRENT_DOWNLOADS:-2}"

# 大文件下载偶尔会被代理断开：失败自动重试（已下完的文件在 uv 缓存里，不会重下）
retry() { local n; for n in 1 2 3 4 5; do "$@" && return 0; echo "[retry $n/5] $*" >&2; sleep $((n * 10)); done; return 1; }

# Python 3.12（与开发环境一致）。uv 默认从 GitHub 下载 Python，国内用 npmmirror 镜像
export UV_PYTHON_INSTALL_MIRROR="${UV_PYTHON_INSTALL_MIRROR:-https://registry.npmmirror.com/-/binary/python-build-standalone}"
[ -d .venv ] || uv venv -q -p 3.12 .venv
export VIRTUAL_ENV="$KIT/.venv"
if [ "$TORCH_SOURCE" = aliyun ]; then
  # torch / torchvision 从阿里云镜像下载到本地（curl 断点续传 + 重试），依赖的 nvidia-* 库走 PIP_INDEX
  MIRROR="https://mirrors.aliyun.com/pytorch-wheels/${TORCH_CUDA}"
  mkdir -p vendor/wheels
  for w in "torch-${TORCH_VERSION}+${TORCH_CUDA}-cp312-cp312-manylinux_2_28_x86_64.whl" \
           "torchvision-${TORCHVISION_VERSION}+${TORCH_CUDA}-cp312-cp312-manylinux_2_28_x86_64.whl"; do
    [ -f "vendor/wheels/$w" ] && continue
    curl -fL --retry 10 --retry-delay 5 --retry-all-errors -C - -o "vendor/wheels/$w.part" "$MIRROR/${w//+/%2B}"
    mv "vendor/wheels/$w.part" "vendor/wheels/$w"
  done
  retry uv pip install -q vendor/wheels/torch-*.whl vendor/wheels/torchvision-*.whl --index-url "$PIP_INDEX"
else
  retry uv pip install -q "torch==${TORCH_VERSION}" "torchvision==${TORCHVISION_VERSION}" --index-url "$TORCH_INDEX"
fi

mkdir -p vendor
if [ ! -d vendor/kohakumoss-0.1.0 ]; then
  .venv/bin/python -m pip --version >/dev/null 2>&1 || uv pip install -q -i "$PIP_INDEX" pip
  .venv/bin/python -m pip download -q -i "$PIP_INDEX" --no-deps --no-binary kohakumoss kohakumoss==0.1.0 -d vendor
  tar xzf vendor/kohakumoss-0.1.0.tar.gz -C vendor
fi
# torch 已装好；KohakuMoss 的其余依赖都从 PIP_INDEX 安装
retry uv pip install -q -e "vendor/kohakumoss-0.1.0[cuda]" "torch==${TORCH_VERSION}" --index-url "$PIP_INDEX"
# ipywidgets：Notebook 里的进度条（没有它，进度条会退回成红色的纯文本，还带一条警告）
retry uv pip install -q -i "$PIP_INDEX" jupyterlab ipykernel ipywidgets nbconvert nbformat matplotlib pandas pillow
.venv/bin/python -m ipykernel install --user --name moss-train --display-name "Python (moss-train: KohakuMoss + torch)" >/dev/null
# 平台自带的 JupyterLab（优云智算：/usr/local/miniconda3）也要装进度条的前端扩展，JupyterLab 重启后生效
if [ -x /usr/local/miniconda3/bin/pip ]; then
  retry /usr/local/miniconda3/bin/pip install -q -i "$PIP_INDEX" jupyterlab_widgets
fi

.venv/bin/python - <<'PY'
import torch, kohakumoss
print("torch", torch.__version__, "cuda", torch.version.cuda, "gpu", torch.cuda.is_available(),
      torch.cuda.get_device_name(0) if torch.cuda.is_available() else "-")
PY
echo SETUP_DONE
