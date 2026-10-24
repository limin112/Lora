#!/usr/bin/env bash
# 安装 ComfyUI（独立 venv，与训练环境互不影响），模型直接用平台共享目录 /model 里 Comfy-Org 打包的 MOSS-Image
set -euo pipefail
KIT="$(cd "$(dirname "$0")" && pwd)"
COMFY_DIR="${COMFY_DIR:-/root/ComfyUI}"
COMFY_REF="${COMFY_REF:-8baf68d53d751216dd95d4f678bf109d82db3442}"   # Comfy-Org/ComfyUI master 2026-10-23，含 MOSS-Image 及其 LoRA 支持
PIP_INDEX="${PIP_INDEX:-https://pypi.tuna.tsinghua.edu.cn/simple}"
MOSS_COMFY_MODELS="${MOSS_COMFY_MODELS:-/model/ModelScope/Comfy-Org/MOSS-Image}"
export PATH="$HOME/.local/bin:/usr/local/miniconda3/bin:$PATH" UV_HTTP_TIMEOUT=120 UV_LINK_MODE=copy \
       UV_PYTHON_INSTALL_MIRROR=https://registry.npmmirror.com/-/binary/python-build-standalone
retry() { for i in 1 2 3 4 5; do "$@" && return 0; echo "retry $i: $*"; sleep 10; done; return 1; }

if [ ! -f "$COMFY_DIR/main.py" ]; then
    mkdir -p "$COMFY_DIR"
    TARBALL="$KIT/vendor/comfyui-$COMFY_REF.tar.gz"   # 国内直连 GitHub 很慢时，可先在别处下载好放到这里
    [ -s "$TARBALL" ] || retry curl -fL --retry 5 -o "$TARBALL" "https://codeload.github.com/Comfy-Org/ComfyUI/tar.gz/$COMFY_REF"
    tar xzf "$TARBALL" -C "$COMFY_DIR" --strip-components=1
    echo "$COMFY_REF" > "$COMFY_DIR/COMFY_REF"
fi
cd "$COMFY_DIR"
[ -d .venv ] || uv venv -p 3.12 .venv
export VIRTUAL_ENV="$COMFY_DIR/.venv"
# torch 复用训练环境下载好的同一份 wheel（阿里云镜像）
retry uv pip install "$KIT"/vendor/wheels/torch-*.whl "$KIT"/vendor/wheels/torchvision-*.whl --index-url "$PIP_INDEX"
# 清华源没同步到的新包（如 comfyui-workflow-templates-media-assets-*）从阿里云源补上
retry uv pip install -r requirements.txt --index-url "$PIP_INDEX" --extra-index-url https://mirrors.aliyun.com/pypi/simple

# 模型：软链到平台共享目录（只读，不占实例磁盘）
for sub in diffusion_models text_encoders vae; do
    mkdir -p "models/$sub"
    for f in "$MOSS_COMFY_MODELS/$sub"/*.safetensors; do
        [ -e "$f" ] && ln -sfn "$f" "models/$sub/$(basename "$f")"
    done
done
mkdir -p models/loras

# moss01 示例工作流：放进一个空的 custom node 的 example_workflows/，在 ComfyUI「模板」里能直接打开
# （经 JupyterLab /proxy/8188/ 访问时，侧栏「已保存的工作流」打不开，模板不受影响）
# 另带一段前端脚本：打开 ComfyUI 时如果还是自带的默认工作流，自动换成「原模型 vs 加 LoRA」对比工作流
mkdir -p custom_nodes/moss01_lora/example_workflows custom_nodes/moss01_lora/web
printf '# moss01 LoRA：示例工作流 + 默认打开对比工作流的前端脚本，没有自定义节点\nNODE_CLASS_MAPPINGS = {}\nNODE_DISPLAY_NAME_MAPPINGS = {}\nWEB_DIRECTORY = "./web"\n' \
    > custom_nodes/moss01_lora/__init__.py
cp "$KIT/comfyui/moss01_lora_t2i.json" "$KIT/comfyui/moss01_leak_compare.json" custom_nodes/moss01_lora/example_workflows/
cp "$KIT/comfyui/moss01_default_workflow.js" custom_nodes/moss01_lora/web/

# 优云智算：给平台自带的 JupyterLab 装 jupyter-server-proxy（ComfyUI 可从 <JupyterLab 地址>/proxy/8188/ 打开，
# JupyterLab 重启后生效），并在 /start.d 放开机自启脚本（平台开机时会运行 /start.d/*.sh）
if [ -x /usr/local/miniconda3/bin/pip ]; then
    retry /usr/local/miniconda3/bin/pip install -q -i "$PIP_INDEX" jupyter-server-proxy
fi
if [ -d /start.d ]; then
    printf '#!/usr/bin/env bash\nexec bash %s/start_comfyui.sh\n' "$KIT" > /start.d/comfyui.sh
fi
echo "COMFY_SETUP_DONE $(date -Is)"
