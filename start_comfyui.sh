#!/usr/bin/env bash
# 启动 ComfyUI（setup_comfyui.sh 装好之后）。默认端口 8188，监听所有地址。
# 浏览器访问：JupyterLab 地址把 /lab... 换成 /proxy/8188/ ；或 SSH 转发：ssh -p <端口> -N -L 8188:localhost:8188 root@<实例地址>
set -euo pipefail
COMFY_DIR="${COMFY_DIR:-/root/ComfyUI}"
PORT="${COMFY_PORT:-8188}"
cd "$COMFY_DIR"
if curl -s -o /dev/null "http://127.0.0.1:$PORT/system_stats"; then
    echo "ComfyUI 已经在运行：端口 $PORT"; exit 0
fi
exec "$COMFY_DIR/.venv/bin/python" main.py --listen 0.0.0.0 --port "$PORT" --disable-auto-launch "$@"
