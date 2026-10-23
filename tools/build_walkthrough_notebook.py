"""Generate moss01_lora_walkthrough.ipynb: a hands-on, step-by-step MOSS-Image LoRA tutorial."""
import sys
from pathlib import Path

import nbformat as nbf

md = nbf.v4.new_markdown_cell
code = nbf.v4.new_code_cell

cells = [
    md("""# 动手训练一个 MOSS-Image 人物 LoRA（上手教程）

用我们已经做好的虚拟人 **Moss**（触发词 `moss01`）的数据，亲手走一遍 LoRA 训练的完整流程。每一步都是「说明 + 可以运行的代码」，**按顺序从上往下运行**即可。

| 步骤 | 做什么 | 大约用时 | 用 GPU |
| --- | --- | --- | --- |
| 0 | 环境和路径 | 几秒 | |
| 1 | 看数据：图片和 caption 长什么样 | 几秒 | |
| 2 | 生成训练集目录 | 约 10 秒 | |
| 3 | 告诉框架数据在哪，看它实际会怎么读数据 | 约 30 秒 | |
| 4 | 缓存：提前算好文本嵌入和图片潜变量 | 约 3 分钟 | ✅ |
| 5 | 训练：后台跑 60 步，边训练边看进度、loss 和验证图 | 约 8 分钟 | ✅ |
| 6 | 用训练好的 LoRA 出图（可以自己改提示词） | 约 3 分钟 | ✅ |
| 7 | 用 KohakuMoss 自带的对比工具比较检查点和强度 | 约 6 分钟 | ✅ |

- **训练框架**：KohakuMossTrainer 0.1.0。这是第三方框架（作者 KohakuBlueleaf），不是 OpenMOSS 官方出品；OpenMOSS 没有发布训练代码，只在 MOSS-Image 的 README 新闻栏里介绍过它。
- **模型**：MOSS-Image-Base（5B DiT + Qwen3.5-9B 文本编码器 + FLUX.2 VAE）。
- **不会影响正式训练**：本教程的所有输出都在 `walkthrough/` 目录；第 6、7 步只**读取**正式训练的检查点。
- **运行环境**：在工具包根目录打开本 Notebook，内核选 **`Python (moss-train: KohakuMoss + torch)`**。用 GPU 的步骤运行前，确认 `GPU` 指定的那张卡是空闲的（`nvidia-smi`）。
- **前提**：已经运行过 `setup_env.sh`（环境）、`download_weights.sh`（权重），并用 `train_moss01.sh` 完成了正式训练（第 6、7 步要用它的检查点）。"""),

    md("## 第 0 步：环境和路径\n\n`CUDA_VISIBLE_DEVICES` 必须在导入 torch 之前设置，所以这一格要最先运行。之后启动的训练、缓存子进程也会继承这些环境变量。"),
    code("""import os
from pathlib import Path

GPU = os.environ.get("MOSS_GPU", "0")         # 本教程只用这一张卡；运行前确认它空闲
os.environ["CUDA_VISIBLE_DEVICES"] = GPU

# 路径都可以用环境变量改；默认值对应 moss-lora-kit 工具包的目录结构（在工具包根目录打开本 Notebook）
KIT = Path(os.environ.get("MOSS_KIT", Path.cwd())).resolve()
PROJECT = Path(os.environ.get("MOSS_PROJECT", KIT / "data/moss01"))          # 数据和训练输出
SOURCE = PROJECT / "source"                                                    # 候选图、清单、selection.json
OFFICIAL_RUN = Path(os.environ.get("MOSS_RUN", PROJECT / "runs/moss01-lora"))  # 正式训练的输出，只读
W = PROJECT / "walkthrough"                                                    # 本教程的所有输出
KM = Path(os.environ.get("MOSS_KOHAKU", KIT / "vendor/kohakumoss-0.1.0"))      # KohakuMoss 源码（含 configs/ scripts/）
KOGINE = Path(os.environ.get("MOSS_KOGINE", KIT / ".venv/bin/kogine"))
WEIGHTS = os.environ.get("MOSS_WEIGHTS", str(KIT / "weights/MOSS-Image-Base"))   # 模型权重目录（HF 格式）
TRIGGER = "moss01"

# 临时文件和编译缓存放在项目目录下
for k, v in {"TMPDIR": "tmp", "XDG_CACHE_HOME": "cache", "TORCHINDUCTOR_CACHE_DIR": "cache/torchinductor",
             "TRITON_CACHE_DIR": "cache/triton"}.items():
    os.environ[k] = str(PROJECT / v)
    Path(os.environ[k]).mkdir(parents=True, exist_ok=True)
os.environ["PYTHONWARNINGS"] = "ignore"
W.mkdir(exist_ok=True)

import subprocess
print(subprocess.run(["nvidia-smi", "--query-gpu=index,name,memory.used,utilization.gpu", "--format=csv,noheader"],
                     capture_output=True, text=True).stdout)
print("使用 GPU", GPU, "| 教程输出目录", W)"""),
    code("""import re
import sys

NOISE = re.compile(r"distutils|addpackage|frozen site|string>|Remainder of file|_distutils_hack|^\\s*$")
ANSI = re.compile(r"\\x1b\\[[0-9;]*m")              # 终端颜色代码


def run(args, show=r".", tail=None):
    \"\"\"在 KohakuMoss 目录里运行一条命令，实时打印匹配 `show` 的输出行（过滤掉进度条和无关告警）。\"\"\"
    proc = subprocess.Popen([str(a) for a in args], cwd=KM, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, env=os.environ.copy())
    keep, pat = [], re.compile(show)
    for raw in proc.stdout:
        for line in ANSI.sub("", raw).replace("\\r", "\\n").split("\\n"):
            if NOISE.search(line) or not pat.search(line):
                continue
            keep.append(line)
            if tail is None:
                print(line[:220], flush=True)
    proc.wait()
    if tail:
        print("\\n".join(l[:220] for l in keep[-tail:]))
    if proc.returncode != 0:
        raise RuntimeError(f"命令失败（返回码 {proc.returncode}）：{' '.join(map(str, args))}")
    return keep


print("helper ready")"""),

    md("""## 第 1 步：看数据

训练数据就是 **一张图 + 一段文字（caption）**。模型学的是：当文字里出现 `moss01` 时，画出的人应该是这个人。

`selection.json` 是我们在挑选页面上确认后导出的清单：选了哪 56 张图、每张图的 caption 由哪 7 个字段组成。"""),
    code("""import collections
import json

sel = json.loads((SOURCE / "selection.json").read_text(encoding="utf-8"))
items = sel["items"]
print(f"选用 {sel['n']} 张，不用 {len(sel['dropped'])} 张：{sel['dropped']}")
print("一条记录长这样：")
print(json.dumps(items[0], ensure_ascii=False, indent=1))"""),
    code("""from IPython.display import display
from PIL import Image

# 随便挑 4 张不同类型的图，看图和 caption 是怎么对应的。可以改成别的编号试试（M02–M48, P01–P20）
SHOW = ["M03", "P01", "P15", "P07"]
by_id = {it["id"]: it for it in items}
for sid in SHOW:
    it = by_id[sid]
    im = Image.open(SOURCE / it["file"]).convert("RGB")
    im.thumbnail((420, 420))
    display(im)
    print(f"{sid}  ({'校服' if it['uniform'] else '便装'})")
    for k, v in it["fields"].items():
        print(f"   {k:10s} {v}")
    print("   caption  ", it["caption"], "\\n")"""),
    md("""**caption 的原则**：会变化的东西（构图、角度、表情、发型、服装、场景、光线）都写进 caption，变成提示词能控制的变量；不变的身份特征（脸、眼睛、发色）不写，让模型把它们学进触发词 `moss01`。

看看整个数据集的分布。分布不均衡的地方，就是训练后容易出问题的地方："""),
    code("""def bucket(s, kind):
    if kind == "framing":
        return "全身" if "full" in s else "半身" if "upper" in s else "特写"
    if s.startswith("back"):
        return "背影"
    if s.startswith("side"):
        return "侧脸-" + ("左" if "left" in s else "右")
    if s.startswith("three"):
        return "3/4侧-" + ("左" if "left" in s else "右")
    return "正脸"


for kind in ["framing", "angle"]:
    print(kind, dict(collections.Counter(bucket(it["fields"][kind], kind) for it in items)))
u = sum(it["uniform"] for it in items)
print(f"服装：校服 {u}，便装 {len(items) - u}（校服占 {u / len(items):.0%}）")"""),

    md("""## 第 2 步：生成训练集目录

KohakuMoss 读取 **kohya 风格**的目录：文件夹名 `<重复次数>_<名字>`，里面每张图配一个同名的 `.txt`：

```
walkthrough/data/train/
└── 1_moss01/
    ├── M02.png
    ├── M02.txt      ← 内容就是这张图的 caption
    ├── M03.png
    └── ...
```

正式训练用的是 `prepare_moss01_for_lora.ipynb` 生成的训练集（多了校验、统计和报告）。这里用最简单的方式再做一遍，看清楚它本质上就是「复制图片 + 写 txt」。"""),
    code("""import shutil

TRAIN_ROOT = W / "data/train"
TRAIN_DIR = TRAIN_ROOT / f"1_{TRIGGER}"
if TRAIN_ROOT.exists():
    shutil.rmtree(TRAIN_ROOT)            # 只删教程自己的目录
TRAIN_DIR.mkdir(parents=True)

for it in items:
    src = SOURCE / it["file"]
    shutil.copyfile(src, TRAIN_DIR / f"{it['id']}{src.suffix.lower()}")
    (TRAIN_DIR / f"{it['id']}.txt").write_text(it["caption"] + "\\n", encoding="utf-8")

files = sorted(p.name for p in TRAIN_DIR.iterdir())
print(len(files), "个文件，前 6 个：", files[:6])
print("M02.txt 的内容：", (TRAIN_DIR / "M02.txt").read_text(encoding="utf-8"))
assert len(files) == 2 * len(items)"""),

    md("""## 第 3 步：告诉框架数据在哪，看它实际会怎么读

KohakuMoss 的配置文件就是一个 Python 文件，里面是一些**大写的变量**（叫 knob）。`use_config(...)` 可以继承另一个配置，再只改需要改的部分。

我们的教程配置继承了正式训练的配置 `moss01-lora.py`（LoRA 参数、caption 规则都一样），只改了：数据路径、单卡、20 步、输出目录。"""),
    code("""CFG_DIR = KM / "configs/user"
if not (CFG_DIR / "moss01-lora.py").exists():          # 还没跑过正式训练：先只生成正式训练的配置
    r = subprocess.run(["bash", str(KIT / "train_moss01.sh")], env={**os.environ, "CONFIG_ONLY": "1"},
                       capture_output=True, text=True)
    print(r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-500:])
    assert (CFG_DIR / "moss01-lora.py").exists(), "生成正式训练配置失败"
train_cfg = CFG_DIR / "walkthrough-lora.py"
data_cfg = CFG_DIR / "walkthrough-lora_data.py"

train_cfg.write_text(f'''\"\"\"上手教程：继承第二版正式训练配置，单卡 60 步。Drives scripts/train/moss.py.\"\"\"
from kohakuengine import use_config

use_config("moss01-lora.py")        # 继承正式训练的全部设置

DATASETS = [{{"source": "kohya", "path": "{TRAIN_ROOT}", "repeat_prefix": "first",
             "artist_from_folder": None, "txt_as": "tags", "include_root": False}}]
PARALLEL = "none"                   # 单卡
DEVICES = (0,)
STEPS = 60                          # 正式训练 1200 步
SCHEDULE = {{"mode": "cosine", "warmup": 5, "end": -1, "min_value": 0.1}}
SAVE_EVERY = 20
SAMPLE_EVERY = 20                   # 每 20 步出一组验证图，训练中途就能看到效果
SAMPLE_PROMPTS = [
    "moss01, upper-body portrait, front view, calm expression, two long braids hairstyle, wearing school uniform: dark green cardigan, white blouse, green ribbon tie, old library with wooden shelves, warm window light",
    "moss01, full-body portrait, front view, walking, long loose straight hair hairstyle, wearing a red knit sweater and jeans, autumn park, golden hour sunlight",
]
LOG_EVERY = 2
OUTPUT_DIR = "{W / 'runs'}"
RUN_NAME = "walkthrough"
''', encoding="utf-8")

data_cfg.write_text(f'''\"\"\"上手教程的数据缓存配置：训练配置的数据设置 + 两个编码器。Drives scripts/data/inspect_data.py, scripts/data/cache_text.py, scripts/data/cache_latents.py.\"\"\"
from kohakuengine import use_config

use_config("walkthrough-lora.py")
TEXT_ENCODER = "kohakumoss.encoders.text_encoder"
TEXT_ENCODER_KWARGS = {{"path": "{WEIGHTS}", "device": "cuda"}}
IMAGE_ENCODER = "kohakumoss.encoders.vae_encoder"
IMAGE_ENCODER_KWARGS = {{"path": "{WEIGHTS}", "device": "cuda"}}
''', encoding="utf-8")

print(train_cfg.read_text(encoding="utf-8"))
run([KOGINE.parent / "kohakumoss-config", "check", train_cfg])"""),
    md("""`inspect_data.py` 会告诉我们**框架实际怎么读这批数据**：

- **catalog**：一共几张图、尺寸分布；
- **plan**：每批放几张图、图片被缩放成什么尺寸（MOSS-Image 按约 1MP 训练，长宽比相近的图分到同一组）；
- **captions**：模型实际看到的 caption。注意 `moss01` 一直在最前面，后面的短语被**打乱**、偶尔被**丢掉**一个，这是一种数据增强，让模型不要死记 caption 的写法。"""),
    code("""out = run([KOGINE, "run", "scripts/data/inspect_data.py", "--config", data_cfg], tail=None,
          show=r"rows|batches|samples_per_batch|top_sizes|x1248|x832|captions|moss01|budget_fill")"""),
    code("""# 同一张图，原始 caption 和框架打乱后的几种写法对比（CAPTION_VARIANTS=8：每张图缓存 8 种写法）
print("原始：", (TRAIN_DIR / "M02.txt").read_text(encoding="utf-8").strip())
import random
tags = (TRAIN_DIR / "M02.txt").read_text(encoding="utf-8").strip().split(", ")
rng = random.Random(0)
for k in range(3):
    rest = [t for t in tags[1:] if rng.random() > 0.1]      # keep_first=1：触发词固定；其余 10% 丢弃
    rng.shuffle(rest)                                        # 打乱顺序
    print(f"写法{k + 1}：", ", ".join([tags[0]] + rest))
print("（这里只是用同样的规则模拟一下，实际写法由框架按种子生成）")"""),

    md("""## 第 4 步：缓存（用 GPU）

训练时每一步都要用到两样东西：

1. **文本嵌入**：caption 经过 Qwen3.5-9B 文本编码器得到的向量。文本编码器有 18GB，而且训练时冻结不动，所以**提前算一次存下来**，训练时就不用加载它。
2. **图片潜变量**：图片经过 VAE 压缩后的表示。扩散模型实际是在潜变量上训练的，同样提前算好。

缓存存在训练集旁边的 `cache/` 目录里，以后数据不变就不用再算。"""),
    code("""run([KOGINE, "run", "scripts/data/cache_text.py", "--config", data_cfg], tail=6, show=r"INFO|WARN|ERROR|wrote|done")
run([KOGINE, "run", "scripts/data/cache_latents.py", "--config", data_cfg], tail=6, show=r"INFO|WARN|ERROR|wrote|done")"""),
    code("""cache_dir = TRAIN_ROOT / "cache"
total = 0
for p in sorted(cache_dir.rglob("*")):
    if p.is_file():
        total += p.stat().st_size
print(f"缓存目录 {cache_dir}：{sum(1 for p in cache_dir.rglob('*') if p.is_file())} 个文件，共 {total / 1e6:.1f} MB")
for d in sorted(x for x in cache_dir.iterdir()):
    print("  ", d.name)"""),

    md("""## 第 5 步：训练（用 GPU，60 步小练习，边训练边看）

正式训练（`train_moss01.sh`）用的关键参数（教程继承了它们）：

| 参数 | 值 | 作用 |
| --- | --- | --- |
| `ALGO` / `DIM` / `ALPHA` | lora / 32 / 32 | LoRA 的秩。越大能学的细节越多，文件也越大 |
| `PRESET` | attn-mlp | LoRA 加在注意力层和 MLP 层上；原模型 5B 参数全部冻结 |
| `LR` | 1e-4 | 学习率 |
| `SCHEDULE` | cosine | 学习率先预热、再按余弦曲线下降 |
| `MAX_TOKENS` | 12288 | 每批的 token 预算；1MP 的图约 4100 个 token，所以每批 2 张 |
| `TEXT_DROP` | 0.1 | 10% 的时候把 caption 换成空文本，让模型也会无条件生成（CFG 需要） |
| `CAPTION` | keep_first=1, shuffle, tag_dropout=0.1 | 触发词固定，其余短语打乱、偶尔丢弃 |
| `STEPS` / `SAVE_EVERY` / `SAMPLE_EVERY` | 1200 / 150 / 300（正式，单卡） | 总步数 / 多久存一次检查点 / 多久出一组验证图 |

**训练放到后台跑**，单元格会马上返回。训练过程中框架不断往磁盘写：

- `metrics.jsonl`：每隔几步一行（步数、loss、学习率、每步耗时）；
- `samples/step_N/`：每 `SAMPLE_EVERY` 步一组验证图；
- `checkpoints/step_N/`：每 `SAVE_EVERY` 步一个检查点（LoRA 权重）。

下一格的 `watch()` 每隔一会儿读一次这些文件，显示进度、loss 曲线和最新的验证图，**不需要任何图形界面**。第一次在一张卡上训练会先花几分钟调优算子，这段时间进度是 0。"""),
    code("""LOG = W / "train.log"
run_dir = W / "runs/walkthrough"
if run_dir.exists():
    shutil.rmtree(run_dir)            # 重新练一次时清掉上一次的教程输出
train_proc = subprocess.Popen([str(KOGINE), "run", "scripts/train/moss.py", "--config", str(train_cfg)],
                              cwd=KM, stdout=open(LOG, "w"), stderr=subprocess.STDOUT,
                              env=os.environ.copy(), start_new_session=True)
print("训练已在后台启动，pid", train_proc.pid, "| 日志", LOG)"""),
    code("""import time

import matplotlib.pyplot as plt
from IPython.display import clear_output


def latest_samples(run_dir, thumb=300):
    \"\"\"把最新一组验证图拼成一行。\"\"\"
    folders = sorted((run_dir / "samples").glob("step_*")) if (run_dir / "samples").exists() else []
    folders = [f for f in folders if any(f.glob("*.png"))]
    if not folders:
        return None, None
    ims = []
    for p in sorted(folders[-1].glob("*.png")):
        im = Image.open(p).convert("RGB")
        im.thumbnail((thumb, thumb))
        ims.append(im)
    row = Image.new("RGB", (sum(i.width for i in ims) + 6 * len(ims), max(i.height for i in ims)), "white")
    x = 0
    for im in ims:
        row.paste(im, (x, 0))
        x += im.width + 6
    return folders[-1].name, row


def watch(run_dir, proc=None, every=20, max_minutes=None):
    \"\"\"每 `every` 秒刷新一次：进度、剩余时间、loss 曲线、最新验证图。训练结束（或超时）自动停止；
    也可以随时中断这个单元格，训练不受影响。\"\"\"
    t0 = time.time()
    while True:
        total = json.loads((run_dir / "config.json").read_text()).get("STEPS") if (run_dir / "config.json").exists() else None
        rows = [json.loads(l) for l in (run_dir / "metrics.jsonl").read_text().splitlines()] if (run_dir / "metrics.jsonl").exists() else []
        rows = [r for r in rows if "loss" in r]
        step = rows[-1]["step"] if rows else 0
        clear_output(wait=True)
        if total:
            done_frac = step / total
            st = sorted(r["step_time"] for r in rows if "step_time" in r)
            eta = f"，按每步 {st[len(st)//2]:.2f} 秒估计还需约 {st[len(st)//2] * (total - step) / 60:.1f} 分钟（不含出图）" if st else ""
            print(f"[{'#' * int(30 * done_frac):<30}] {step}/{total} 步{eta}")
        else:
            print("训练准备中（加载模型、调优算子）……")
        if rows:
            print(f"最新：loss={rows[-1]['loss']:.4f}  lr={rows[-1]['lr']:.2e}")
            fig, ax = plt.subplots(figsize=(7, 2.4))
            ax.plot([r["step"] for r in rows], [r["loss"] for r in rows], marker=".")
            ax.set_xlabel("step")
            ax.set_ylabel("loss")
            plt.show()
        name, row = latest_samples(run_dir)
        if row is not None:
            print("最新验证图：", name)
            display(row)
        finished = (proc is not None and proc.poll() is not None) or (run_dir / "export").exists()
        if finished:
            code = proc.returncode if proc is not None else 0
            print("训练结束" if not code else f"训练出错（返回码 {code}），日志最后几行：")
            if code:
                print("\\n".join(LOG.read_text(errors="ignore").splitlines()[-15:]))
            return
        if max_minutes and time.time() - t0 > max_minutes * 60:
            print(f"已监控 {max_minutes} 分钟，先停下（训练还在继续），想继续看就再运行这一格")
            return
        time.sleep(every)


watch(run_dir, proc=train_proc)"""),
    code("""# 训练结束后：检查点和导出的 LoRA
print("检查点：", sorted(p.name for p in (run_dir / "checkpoints").iterdir()))
print("导出的 LoRA：", sorted(p.name for p in (run_dir / "export").iterdir()))

# 想提前结束训练（比如效果已经够了），运行这一行：
# os.killpg(train_proc.pid, 15)"""),
    md("""60 步还学不会这个人，但你能在验证图里看到它**一点点往 Moss 靠**。loss 曲线一直上下波动、看不出趋势，这是扩散模型的正常现象，**判断效果要看图**（第 6、7 步）。

同一个 `watch()` 也能看**正式训练**。正式训练还在跑的时候运行下一格，就能实时看到它的进度和最新验证图；如果已经跑完，会直接显示最终状态："""),
    code("""watch(OFFICIAL_RUN, max_minutes=1)"""),
    md("""## 第 6 步：用训练好的 LoRA 出图（用 GPU）

用**正式训练**（`train_moss01.sh`）的检查点。`MossPipeline` 是 KohakuMoss 的推理接口：加载模型时用 `adapters=[(文件, 强度)]` 把 LoRA 挂上去。

采样参数用 OpenMOSS 用户指南（`USERGUIDE.md`）里给 MOSS-Image-Base 的推荐值：**≥50 步、CFG 3、shift 5、Euler、跳过第 22 层**（Base 模型没有做过蒸馏，步数不能太少）。

**可以改的地方**：`CKPT_STEP`（用哪个检查点）、`STRENGTH`（LoRA 强度）、`PROMPTS`（提示词，记得带上 `moss01`）。改完重新运行这两格。"""),
    code("""import gc

import torch
from kohakumoss.inference import MossPipeline

AVAILABLE = sorted(int(p.name[5:]) for p in (OFFICIAL_RUN / "checkpoints").glob("step_*"))
CKPT_STEP = AVAILABLE[(len(AVAILABLE) * 3) // 4 - 1]   # 默认取 3/4 处的检查点；可以改成 AVAILABLE 里的任意一个
print("可用的检查点：", AVAILABLE, "| 本次使用：", CKPT_STEP)
STRENGTH = 1.0                  # LoRA 强度，0.7 左右身份会淡一些
ckpt = OFFICIAL_RUN / f"checkpoints/step_{CKPT_STEP:08d}/trainable.safetensors"
assert ckpt.exists(), f"没有这个检查点：{ckpt}"

pipe = MossPipeline.from_pretrained(WEIGHTS, dtype=torch.bfloat16, adapters=[(str(ckpt), STRENGTH)])
print("模型和 LoRA 加载完成：", ckpt.parent.name, "强度", STRENGTH)"""),
    code("""PROMPTS = [
    "moss01, full-body portrait, front view, walking, long loose straight hair hairstyle, wearing a denim jacket and a white t-shirt, busy city street, overcast daylight",
    "moss01, upper-body portrait, three-quarter view facing left, bright smile, low bun hairstyle, wearing a yellow raincoat, rainy street at night, neon lights",
]
out = pipe.generate(PROMPTS, sizes=(1024, 1024), seeds=[0] * len(PROMPTS), steps=50, cfg=3.0, shift=5.0)
for p, im in zip(PROMPTS, out.images):
    im.thumbnail((640, 640))
    display(im)
    print(p, "\\n")"""),
    code("""# 用完释放显存，否则第 7 步会不够
del pipe
gc.collect()
torch.cuda.empty_cache()
print("显存已释放")"""),

    md("""## 第 7 步：用 KohakuMoss 自带的工具对比检查点和强度（用 GPU）

`scripts/sample/compare_grid.py` 是 KohakuMoss 自带的对比工具：**模型只加载一次**，先用原模型（不加 LoRA）出图，再把每个检查点依次挂上去出图；**同一个提示词用同一个随机种子**，所以差别只来自 LoRA。

看图时关注：

- **身份**：步数越多越像 Moss；
- **过拟合**：步数太多时，提示词里的便装、全身构图会被拉回训练集的样子（校服、半身）；
- **强度**：同一个检查点，强度 0.7 和 1.0 的区别。"""),
    code("""AVAILABLE = sorted(int(p.name[5:]) for p in (OFFICIAL_RUN / "checkpoints").glob("step_*"))
GRID_STEPS = [AVAILABLE[0], AVAILABLE[(len(AVAILABLE) * 3) // 4 - 1], AVAILABLE[-1]]   # 最早、3/4 处、最后
print("对比的检查点：", GRID_STEPS)
grid_cfg = CFG_DIR / "walkthrough-grid.py"
ckpts = [(str(OFFICIAL_RUN / f"checkpoints/step_{s:08d}/trainable.safetensors"), 1.0) for s in GRID_STEPS]
ckpts.append((ckpts[1][0], 0.7))
labels = [f"step {s}" for s in GRID_STEPS] + [f"step {GRID_STEPS[1]} x0.7"]
grid_cfg.write_text(f'''\"\"\"上手教程：原模型 + 3 个检查点 + 1 个降低强度的对比。Drives scripts/sample/compare_grid.py.\"\"\"
WEIGHTS = "{WEIGHTS}"
CHECKPOINTS = {ckpts!r}
LABELS = {labels!r}
PROMPTS = [
    "moss01, full-body portrait, front view, standing, long loose straight hair hairstyle, wearing a red knit sweater and jeans, autumn park, golden hour sunlight",
    "moss01, close-up portrait, side profile facing left, calm expression, low bun hairstyle, wearing a gray turtleneck sweater, plain gray studio backdrop, soft studio light",
]
SEEDS = [0, 0]
STEPS = 50
CFG = 3.0
SHIFT = 5.0
GRID_LAYOUT = "prompt-cols"
OUT = "{W / 'grid'}"
''', encoding="utf-8")
print(grid_cfg.read_text(encoding="utf-8"))
run([KOGINE, "run", "scripts/sample/compare_grid.py", "--config", grid_cfg], tail=4, show=r"INFO|ERROR")
g = Image.open(W / "grid/grid.png")
g.thumbnail((1600, 1600))
display(g)"""),

    md("""## 走完了

| 你做了什么 | 对应的正式流程 |
| --- | --- |
| 第 1–2 步：看数据、生成训练集 | `prepare_moss01_for_lora.ipynb` |
| 第 3–4 步：配置、检查数据、缓存 | `train_moss01.sh` 前两步 |
| 第 5 步：训练 | `train_moss01.sh` 第三步 |
| 第 6–7 步：出图、对比 | `sample.py` / `compare_grid.py` + 盲评页面 |

想自己再练一次，可以改第 3 步配置里的 `STEPS`、`LR`、`DIM`，或者在第 2 步换一批图，然后从第 3 步重新运行。教程的输出都在 `walkthrough/`，删掉这个目录就能从头再来。"""),
]

nb = nbf.v4.new_notebook(cells=cells, metadata={
    "kernelspec": {"name": "moss-train", "display_name": "Python (moss-train: KohakuMoss + torch)", "language": "python"},
    "language_info": {"name": "python"},
})
out = Path(sys.argv[1] if len(sys.argv) > 1 else "moss01_lora_walkthrough.ipynb")
nbf.write(nb, out)
print("wrote", out)
