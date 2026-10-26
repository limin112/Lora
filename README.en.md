# moss-lora-kit: Malfoy's Girlfriend · MOSS-Image Character LoRA Training Kit

[简体中文](README.md) | **English** | [日本語](README.ja.md)

An end-to-end workflow for training a character LoRA with [MOSS-Image](https://github.com/OpenMOSS/MOSS-Image) (OpenMOSS, Apache-2.0): environment setup, dataset preparation, training, live previews, and output comparisons. The creative theme is **“Malfoy's Girlfriend”**, featuring the fictional character **Moss** (trigger word: `moss01`).

![MOSS-Image character LoRA tutorial cover](docs/images/cover_5x2_moss_sakura.jpg)

**Tutorial and cloud image:** [Read my X / Twitter tutorial](https://x.com/MinLiBuilds/status/2114617833787470247?s=20) · [Open the Compshare training image](https://www.compshare.cn/images/DsDLGij1oUEb?referral_code=D8gyFELBBX7EvgT8sPgltW&ytag=GPU_YY_YX_X_shijiange1026)

The linked tutorial, notebooks, and screenshots are in Chinese. This README provides English instructions; filenames and workflow names remain unchanged.

- Training framework: [KohakuMossTrainer](https://github.com/KohakuBlueleaf/KohakuMossTrainer) 0.1.0 (third-party; PyPI package: `kohakumoss`).
- Model: MOSS-Image-Base (bf16 DiT + Qwen3.5-9B text encoder + FLUX.2 VAE). The text encoder is frozen during training. KohakuMoss 0.1.0 requires weights in **HF directory format** (`transformer/ text_encoder/ tokenizer/ vae/`); ComfyUI's single-file packages are for inference only.
- GPU: one NVIDIA GPU with at least 24GB VRAM (tested on an RTX 4090 48GB).

## Character previews

These are actual outputs from MOSS-Image with the character LoRA loaded, showing Moss with different hairstyles, outfits, and settings. The cover above is a tutorial illustration; use the outputs below to judge generation quality.

![Character LoRA outputs: teacher, cherry blossoms, short hair, academy, beach, and café](docs/images/moss01_lora_showcase.jpg)

<details>
<summary>Compare training checkpoints at 300 / 600 / 900 / 1200 steps</summary>

Each row is a checkpoint. Columns show a school uniform, a red sweater, a full-body beach portrait, a left-side profile, and a prompt without `moss01`. Compare identity consistency, outfit changes, and prompt adherence when choosing a checkpoint.

![Five validation scenarios across four training checkpoints](docs/images/moss01_ucloud_grid.jpg)

</details>

## Quick start

### A. Use the shared Compshare image (environment preinstalled)

[Open the Compshare image page](https://www.compshare.cn/images/DsDLGij1oUEb?referral_code=D8gyFELBBX7EvgT8sPgltW&ytag=GPU_YY_YX_X_shijiange1026), create an instance from it, then follow the instructions below.

The image includes the Python environment, KohakuMoss, sample data, model weights (`weights/MOSS-Image-Base/`, HF format, about 27GB), and the results of a complete training run (`data/moss01/runs/`).

**Open the tutorial:**

1. Create an RTX 4090 instance from the image. Once it is running, click its **JupyterLab** button in the console's instance list. The platform includes the access token automatically. The adjacent **ComfyUI** button opens ComfyUI directly (see below).

   ![JupyterLab and ComfyUI buttons in the console](docs/images/console_buttons.png)

2. JupyterLab's file browser starts at the system root `/`. Double-click **`root`** → **`moss-lora-kit`** → **`moss01_lora_walkthrough.ipynb`**.

   ![Open the root folder first](docs/images/jupyter_root.png)

   ![Open moss-lora-kit and the tutorial notebook](docs/images/jupyter_kit_files.png)

3. Select **`Python (moss-train: KohakuMoss + torch)`** as the kernel. If no selection dialog appears, click the kernel name in the notebook's upper-right corner.

   ![The moss-train kernel in the upper-right corner](docs/images/jupyter_kernel.png)

4. Select the first code cell and press **Shift + Enter** to run it and advance. Work through the notebook starting at step 0. Seeing `使用 GPU 0` (“Using GPU 0”) and GPU usage information in step 0 confirms the environment is working.

**Full training run:** complete tutorial steps 0–5, open a JupyterLab terminal (File → New → Terminal), and run:

```bash
cd /root/moss-lora-kit && bash train_moss01.sh
```

A single-GPU run takes about 65 minutes for 1200 steps. During training, run `watch(OFFICIAL_RUN)` in tutorial step 5 to monitor progress and validation images. After training, use steps 6 and 7 to generate images and compare checkpoints. On a single-GPU instance, **do not run the tutorial's practice training and the full training run simultaneously**.

**You can leave ComfyUI running:** after generating images, it keeps models in VRAM (about 25GB). The notebook's GPU steps and `train_moss01.sh` automatically ask ComfyUI to release VRAM before starting. However, do not generate images in ComfyUI while training or generating images in the notebook.

**Optional local access:** forward port 8888 over SSH, then open `http://localhost:8888/lab`. The token is stored in the instance's `JUPYTER_TOKEN` environment variable:

```bash
ssh -p <port> -N -L 8888:localhost:8888 root@<instance-address>
```

### B. Install from scratch on a new machine

```bash
cd moss-lora-kit
bash setup_env.sh         # Python 3.12 + torch(cu130) + KohakuMoss + Jupyter kernel; about 10 minutes
                         # Older drivers: TORCH_CUDA=cu128 bash setup_env.sh
bash download_weights.sh # Download MOSS-Image-Base from ModelScope (HF format, about 27GB)
```

Then:

1. Run `prepare_moss01_for_lora.ipynb` to build `data/moss01/data/train/1_moss01/` (images and matching `.txt` captions) from `data/moss01/source/selection.json`, validate it, and calculate statistics.
2. Train with `bash train_moss01.sh` (GPU 0 by default; 1200 steps, about one hour). For multiple GPUs, use `GPUS=0,1,2 bash train_moss01.sh`; the step count is adjusted automatically for the number of GPUs.
3. Follow `moss01_lora_walkthrough.ipynb`, or generate images directly with your trained checkpoint.

## Directory structure

```text
moss-lora-kit/
├── setup_env.sh                       # Install the environment
├── download_weights.sh               # Download weights
├── train_moss01.sh                    # Generate config → cache → train
├── start_jupyter.sh                   # Fallback if JupyterLab is not already running
├── setup_comfyui.sh / start_comfyui.sh # Install / start ComfyUI
├── export_comfy.sh                    # Export a checkpoint as a ComfyUI LoRA
├── comfyui/                           # moss01 workflows (UI and API formats)
├── prepare_moss01_for_lora.ipynb       # Build and validate the dataset
├── moss01_lora_walkthrough.ipynb       # Data → training with live previews → generation → comparison
├── tools/
│   ├── build_*_notebook.py            # Generate the two notebooks
│   ├── build_comfy_workflow.py / comfy_smoke_test.py # Workflow generation / generation smoke test
│   ├── nbcheck.py / justified_collage.py
│   └── dataset/                      # Shot lists, supplemental shots, AI suggestions, selection page
├── data/moss01/
│   ├── source/                       # Candidates M01–M48 and P01–P20, manifests, selection.json
│   ├── data/train/1_moss01/           # Training data generated by the preparation notebook
│   └── runs/moss01-lora/              # checkpoints/, samples/, metrics.jsonl, export/
├── weights/MOSS-Image-Base/           # HF format: transformer/, text_encoder/, tokenizer/, vae/
└── vendor/kohakumoss-0.1.0/           # Source downloaded by setup_env.sh; includes configs/ and scripts/
```

## Use your own data

Look at the variation in framing, angles, expressions, and clothing in the example training set for the fictional character Moss:

![Moss training set: varied angles, expressions, framing, and clothing](docs/images/moss01_train_set.jpg)

Put images in one folder, each paired with a `.txt` file of the same basename. Captions start with the trigger word:

```text
moss01, full-body portrait, side profile facing right, gazing out of a window, low bun hairstyle,
wearing school uniform: white blouse, dark green vest, plaid pleated skirt, knee socks, loafers,
candlelit dining hall, warm candlelight
```

Caption guidelines: **describe what varies** (framing, angle, expression, hairstyle, clothing, setting, lighting); **omit fixed identity traits** (face, eyes, hair color, which the trigger word should learn). **Describe what is actually in the image**, and use consistent wording for the same concept.

`tools/dataset/` contains the scripts used to create the Moss dataset: shot lists, supplemental shot lists, and a selection page with AI-prefilled suggestions and human review before exporting `selection.json`. They assume the `data/moss01/source/` layout; adapt them for other datasets.

## Use your trained LoRA

### ComfyUI (preinstalled in the image)

The image includes ComfyUI at `/root/ComfyUI` (Comfy-Org master, with native MOSS-Image support). It starts automatically on port 8188. Models are symlinked from `/model/ModelScope/Comfy-Org/MOSS-Image/`, so they do not consume instance disk space.

1. **Open:** click the instance's **ComfyUI** button in the console. If unavailable, open JupyterLab and replace `/lab` and everything after it in the URL with **`/proxy/8188/`**. Keep the trailing slash.
2. **Export a LoRA:** after training, run this in a JupyterLab terminal (the number is the checkpoint step):
   ```bash
   cd /root/moss-lora-kit && bash export_comfy.sh 900
   ```
   This creates `/root/ComfyUI/models/loras/moss01.safetensors`. The image already includes exports from steps 300, 600, 900, and 1200: `moss01_s300`, `moss01_s600`, `moss01`, and `moss01_s1200`.
3. **Compare base vs. LoRA:** the first launch automatically opens `moss01_原模型vsLoRA对比`. Enter a prompt in the upper-left field without `moss01`, then click Run (`运行`). It produces three images with the same seed: base model / LoRA without `moss01` / LoRA with `moss01`, taking about two minutes. The default is a greenhouse fashion portrait. Change the LoRA file or strength to compare settings.
4. **Normal generation:** open Templates (`模板`) → Extensions (`扩展`) → **moss01_lora** → `moss01_lora_t2i`. The workflow uses MOSS-Image Base (bf16) + moss01 LoRA, 50 steps, CFG 3, Euler, and Skip Layer Guidance at layer 22. Edit the prompt and click Run. A 1024×1024 image takes about 45 seconds on the tested RTX 4090 48GB. The comparison workflow `moss01_leak_compare` is in the same location.
5. When using `/proxy/8188/`, saved files in the Workflows sidebar cannot be opened because the proxy rewrites paths. Export files through the menu instead. SSH forwarding avoids this limitation: `ssh -p <port> -N -L 8188:localhost:8188 root@<instance-address>`, then open `http://localhost:8188`.

On another machine, install with `bash setup_comfyui.sh` (a separate venv, independent of training) and start with `bash start_comfyui.sh`. Use a ComfyUI version newer than 2026-10-16. Outside Compshare, download models from [Comfy-Org/MOSS-Image](https://huggingface.co/Comfy-Org/MOSS-Image) into the corresponding directories under `ComfyUI/models/`.

### Base model vs. LoRA example

Three outputs using the same prompt and seed: base model on the left, LoRA without `moss01` in the middle, and LoRA with `moss01` on the right. This also shows a limitation: loading the LoRA affects appearance even without the trigger word. See the notes below.

![Greenhouse portrait: base model, LoRA without trigger, LoRA with trigger](docs/images/moss01_leak_compare_greenhouse.jpg)

### Python

Use `kohakumoss.inference.MossPipeline.from_pretrained(weights_directory, adapters=[(checkpoint, 1.0)])`; see tutorial step 6.

## Licenses and notes

- MOSS-Image: Apache-2.0. KohakuMoss: KohakuMoss License 1.0.
- The sample images were generated from reference images with Codex (gpt-image-2). The character is fictional, and the samples are for learning and research only. Clothing and settings evoke a British boarding-school aesthetic similar to Harry Potter. Do not use the sample material commercially.
- Known limitations: school uniforms account for 79% of the sample dataset, and left-facing angles are underrepresented. This uses a basic training approach with only Moss images and no regularization images. Loading the LoRA shifts unspecified appearance, ethnicity, and apparent age toward Moss, with little difference between prompts with and without `moss01`. Explicitly prompted hair color, eye color, and gender are not affected in these tests. Load this LoRA only when generating Moss. Use the `moss01_leak_compare` workflow to examine this behavior.
