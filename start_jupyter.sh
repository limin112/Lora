#!/usr/bin/env bash
# 备用：机器上没有现成的 JupyterLab 时才需要（优云智算的实例已自带 8888 端口的 JupyterLab，直接选 moss-train 内核即可）。
# 启动 JupyterLab（在工具包根目录），默认端口 8890。访问密码：环境变量 JUPYTER_TOKEN，未设置则随机生成并打印。
set -euo pipefail
KIT="$(cd "$(dirname "$0")" && pwd)"
cd "$KIT"
TOKEN="${JUPYTER_TOKEN:-$(openssl rand -hex 16)}"
echo "JupyterLab: http://<主机IP>:${JUPYTER_PORT:-8890}/lab?token=$TOKEN"
exec .venv/bin/jupyter lab --ip=0.0.0.0 --port="${JUPYTER_PORT:-8890}" --no-browser --allow-root \
     --IdentityProvider.token="$TOKEN" --ServerApp.root_dir="$KIT"
