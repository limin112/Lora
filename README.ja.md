# moss-lora-kit：マルフォイの彼女 · MOSS-Image 人物 LoRA 学習キット

[简体中文](README.md) | [English](README.en.md) | **日本語**

[MOSS-Image](https://github.com/OpenMOSS/MOSS-Image)（OpenMOSS、Apache-2.0）で人物 LoRA を学習するための一連の手順をまとめたキットです。環境構築、データ準備、学習、学習中のプレビュー、生成結果の比較まで扱います。創作テーマは「**マルフォイの彼女（马尔福女友）**」。サンプルには架空の人物 **Moss**（トリガーワード：`moss01`）を使用しています。

![MOSS-Image 人物 LoRA チュートリアルのカバー](docs/images/cover_5x2_moss_sakura.jpg)

**チュートリアルと環境イメージ：** [作者の X / Twitter チュートリアルを読む](https://x.com/MinLiBuilds/status/2114617833787470247?s=20) · [優雲智算（Compshare）の学習用イメージを開く](https://www.compshare.cn/images/DsDLGij1oUEb?referral_code=D8gyFELBBX7EvgT8sPgltW&ytag=GPU_YY_YX_X_shijiange1026)

リンク先のチュートリアル、Notebook、スクリーンショットは中国語です。この README では操作手順を日本語で説明し、ファイル名とワークフロー名はそのまま記載しています。

- 学習フレームワーク：[KohakuMossTrainer](https://github.com/KohakuBlueleaf/KohakuMossTrainer) 0.1.0（サードパーティ製、PyPI パッケージ名：`kohakumoss`）。
- モデル：MOSS-Image-Base（bf16 DiT + Qwen3.5-9B テキストエンコーダー + FLUX.2 VAE）。学習中はテキストエンコーダーを固定します。KohakuMoss 0.1.0 の学習には **HF ディレクトリ形式**の重み（`transformer/ text_encoder/ tokenizer/ vae/`）が必要です。ComfyUI 向けの単一ファイル形式は推論専用です。
- GPU：VRAM 24GB 以上の NVIDIA GPU 1 枚（RTX 4090 48GB で動作確認）。

## 生成例

以下は MOSS-Image に人物 LoRA を適用して実際に生成した画像です。髪型、服装、場面を変えた Moss を確認できます。上のカバーはチュートリアル用のビジュアルです。生成品質の参考には、こちらの実際の出力をご覧ください。

![人物 LoRA の生成例：教師、桜、ショートヘア、学院、海辺、カフェ](docs/images/moss01_lora_showcase.jpg)

<details>
<summary>300 / 600 / 900 / 1200 ステップの学習結果を比較する</summary>

各行がチェックポイント、各列がテスト条件です。左から制服、赤いセーター、海辺の全身像、左側面の顔、`moss01` を書かないプロンプトを並べています。人物の一貫性、服装の変化、プロンプトへの追従を比較してチェックポイントを選べます。

![4 つのチェックポイントと 5 つの検証条件の比較](docs/images/moss01_ucloud_grid.jpg)

</details>

## クイックスタート

### A. 優雲智算の共有イメージを使う（環境構築済み）

[優雲智算のイメージページを開き](https://www.compshare.cn/images/DsDLGij1oUEb?referral_code=D8gyFELBBX7EvgT8sPgltW&ytag=GPU_YY_YX_X_shijiange1026)、このイメージからインスタンスを作成して、以下の手順でチュートリアルを開きます。

イメージには Python 環境、KohakuMoss、サンプルデータ、モデルの重み（`weights/MOSS-Image-Base/`、HF 形式、約 27GB）、および学習を最後まで実行した結果（`data/moss01/runs/`）が含まれています。

**チュートリアルの開き方：**

1. イメージから RTX 4090 のインスタンスを作成します。起動したら、管理画面のインスタンス一覧で **JupyterLab** ボタンを押します。アクセストークンは自動で付与されます。隣の **ComfyUI** ボタンからは ComfyUI を直接開けます（後述）。

   ![管理画面の JupyterLab と ComfyUI ボタン](docs/images/console_buttons.png)

2. JupyterLab のファイルブラウザーはシステムのルート `/` から始まります。**`root`** → **`moss-lora-kit`** → **`moss01_lora_walkthrough.ipynb`** の順にダブルクリックします。

   ![最初に root フォルダーを開く](docs/images/jupyter_root.png)

   ![moss-lora-kit に移動し、チュートリアルを開く](docs/images/jupyter_kit_files.png)

3. カーネルに **`Python (moss-train: KohakuMoss + torch)`** を選びます。選択ダイアログが出ない場合は、Notebook 右上のカーネル名をクリックして切り替えます。

   ![右上に表示される moss-train カーネル](docs/images/jupyter_kernel.png)

4. 最初のコードセルを選び、**Shift + Enter** で実行して次のセルに進みます。ステップ 0 から順に実行してください。ステップ 0 で `使用 GPU 0`（GPU 0 を使用）と GPU 使用状況が表示されれば、環境は正常です。

**本番の学習：** チュートリアルのステップ 0〜5 を終えてから、JupyterLab でターミナルを開き（File → New → Terminal）、次を実行します。

```bash
cd /root/moss-lora-kit && bash train_moss01.sh
```

GPU 1 枚で 1200 ステップ、所要時間は約 65 分です。学習中はステップ 5 の `watch(OFFICIAL_RUN)` で進捗と検証画像を確認できます。学習後はステップ 6、7 で画像生成とチェックポイント比較を行います。GPU が 1 枚の場合、**チュートリアルの練習用学習と本番の学習を同時に実行しないでください**。

**ComfyUI は起動したままで構いません：** 画像生成後はモデルが VRAM に残ります（約 25GB）。Notebook の GPU を使うステップや `train_moss01.sh` は、開始前に ComfyUI へ VRAM 解放を自動で要求します。ただし、学習中や Notebook での画像生成中は、ComfyUI で同時に画像生成しないでください。

**ローカルから開く場合（任意）：** SSH でポート 8888 を転送し、ブラウザーで `http://localhost:8888/lab` を開きます。トークンはインスタンスの環境変数 `JUPYTER_TOKEN` にあります。

```bash
ssh -p <ポート> -N -L 8888:localhost:8888 root@<インスタンスのアドレス>
```

### B. 新しいマシンに最初からインストールする

```bash
cd moss-lora-kit
bash setup_env.sh         # Python 3.12 + torch(cu130) + KohakuMoss + Jupyter カーネル。約 10 分
                         # 古いドライバーの場合：TORCH_CUDA=cu128 bash setup_env.sh
bash download_weights.sh # ModelScope から MOSS-Image-Base を取得（HF 形式、約 27GB）
```

続いて、以下を実行します。

1. `prepare_moss01_for_lora.ipynb` を実行します。`data/moss01/source/selection.json` に基づいて、画像と同名の `.txt` キャプションを含む `data/moss01/data/train/1_moss01/` を作成し、検証と統計集計を行います。
2. `bash train_moss01.sh` で学習します（デフォルトは GPU 0 のみ、1200 ステップ、約 1 時間）。複数 GPU の場合は `GPUS=0,1,2 bash train_moss01.sh` を使います。ステップ数は GPU 数に応じて自動調整されます。
3. `moss01_lora_walkthrough.ipynb` を順に進めるか、学習済みチェックポイントで直接画像を生成します。

## ディレクトリ構成

```text
moss-lora-kit/
├── setup_env.sh                       # 環境構築
├── download_weights.sh               # 重みのダウンロード
├── train_moss01.sh                    # 設定生成 → キャッシュ → 学習
├── start_jupyter.sh                   # JupyterLab が起動していない場合の予備スクリプト
├── setup_comfyui.sh / start_comfyui.sh # ComfyUI のインストール / 起動
├── export_comfy.sh                    # チェックポイントを ComfyUI 用 LoRA に変換
├── comfyui/                           # moss01 ワークフロー（UI 形式 / API 形式）
├── prepare_moss01_for_lora.ipynb       # データセット生成と検証
├── moss01_lora_walkthrough.ipynb      # データ確認 → 学習とプレビュー → 生成 → 比較
├── tools/
│   ├── build_*_notebook.py            # 2 つの Notebook の生成スクリプト
│   ├── build_comfy_workflow.py / comfy_smoke_test.py # ワークフロー生成 / 画像生成テスト
│   ├── nbcheck.py / justified_collage.py
│   └── dataset/                      # 構図一覧、追加画像一覧、AI 提案、選定ページ
├── data/moss01/
│   ├── source/                       # 候補 M01–M48、追加 P01–P20、一覧、selection.json
│   ├── data/train/1_moss01/           # 準備用 Notebook が生成する学習データ
│   └── runs/moss01-lora/              # checkpoints/、samples/、metrics.jsonl、export/
├── weights/MOSS-Image-Base/           # HF 形式：transformer/、text_encoder/、tokenizer/、vae/
└── vendor/kohakumoss-0.1.0/           # setup_env.sh が取得するソース。configs/、scripts/ を含む
```

## 自分のデータを使う

まずはサンプルの構図、角度、表情、服装のバリエーションを確認してください。以下は架空の人物 Moss の学習に使用する素材の一覧です。

![Moss の学習データ：角度、表情、構図、服装のバリエーション](docs/images/moss01_train_set.jpg)

学習データは 1 つのフォルダーにまとめ、各画像に同じベース名の `.txt` を付けます。キャプションはトリガーワードから始めます。

```text
moss01, full-body portrait, side profile facing right, gazing out of a window, low bun hairstyle,
wearing school uniform: white blouse, dark green vest, plaid pleated skirt, knee socks, loafers,
candlelit dining hall, warm candlelight
```

キャプションの原則は、**変化する要素を書く**こと（構図、角度、表情、髪型、服装、場面、光）。**固定した人物の特徴は書かず**、顔、目、髪色などはトリガーワードに学習させます。**画像に実際に写っている内容を書く**こと、同じ概念には同じ表現を使うことも大切です。

`tools/dataset/` には Moss データセットの制作に使ったスクリプトがあります。構図一覧、追加画像一覧、および AI が提案を事前入力し、人が確認してから `selection.json` を出力する選定ページです。`data/moss01/source/` の構成を前提としているため、別のデータでは適宜変更してください。

## 学習した LoRA を使う

### ComfyUI（イメージにインストール済み）

イメージ内の `/root/ComfyUI` には、MOSS-Image を標準でサポートする Comfy-Org master の ComfyUI が入っています。起動時にポート 8188 で自動起動します。モデルは共有ディレクトリ `/model/ModelScope/Comfy-Org/MOSS-Image/` へのシンボリックリンクを使用するため、インスタンスのディスク容量を消費しません。

1. **開く：** 管理画面の **ComfyUI** ボタンを押します。ボタンがない環境では、JupyterLab の URL の `/lab` 以降を **`/proxy/8188/`** に置き換えます。末尾のスラッシュを省略しないでください。
2. **LoRA をエクスポート：** 学習後、JupyterLab のターミナルで次を実行します。数値はチェックポイントのステップ数です。
   ```bash
   cd /root/moss-lora-kit && bash export_comfy.sh 900
   ```
   `/root/ComfyUI/models/loras/moss01.safetensors` が生成されます。イメージには 300、600、900、1200 ステップのエクスポート済み LoRA（`moss01_s300`、`moss01_s600`、`moss01`、`moss01_s1200`）が含まれています。
3. **元モデルと LoRA を比較：** 初回起動時には `moss01_原模型vsLoRA对比` が自動で開きます。左上に `moss01` を含めずにプロンプトを入力し、「运行」（Run）を押します。同じシードで、元モデル / LoRA・トリガーなし / LoRA・トリガーありの 3 枚を約 2 分で生成します。初期プロンプトは温室でのファッションポートレートです。LoRA ファイルや強度を変更して比較できます。
4. **通常の画像生成：** 左側の「模板」（Templates）→「扩展」（Extensions）→ **moss01_lora** → `moss01_lora_t2i` を開きます。MOSS-Image Base（bf16）+ moss01 LoRA、50 ステップ、CFG 3、Euler、Skip Layer Guidance の第 22 層が設定済みです。プロンプトを編集して実行してください。RTX 4090 48GB で、1024×1024 の画像 1 枚に約 45 秒かかります。比較用の `moss01_leak_compare` も同じ場所にあります。
5. `/proxy/8188/` 経由では、プロキシによるパスの書き換えにより、サイドバーのワークフローに保存したファイルを開けません。保存する場合はメニューからファイルにエクスポートしてください。`ssh -p <ポート> -N -L 8188:localhost:8188 root@<インスタンスのアドレス>` で転送し、`http://localhost:8188` を開く方法ではこの制限はありません。

別のマシンでは、`bash setup_comfyui.sh` でインストールし（学習環境と独立した venv）、`bash start_comfyui.sh` で起動します。2026-10-16 より後の ComfyUI が必要です。優雲智算以外では、[Comfy-Org/MOSS-Image](https://huggingface.co/Comfy-Org/MOSS-Image) からモデルを取得し、`ComfyUI/models/` 内の対応するディレクトリへ配置してください。

### 元モデルと LoRA の比較例

同じプロンプトとシードによる比較です。左は元モデル、中央は LoRA を読み込んで `moss01` を書かなかった場合、右は LoRA を読み込んで `moss01` を書いた場合です。トリガーワードがなくても人物の外見に影響するという、現在のサンプルの制約も確認できます。使用上の注意は末尾をご覧ください。

![温室のポートレート：元モデル、LoRA・トリガーなし、LoRA・トリガーあり](docs/images/moss01_leak_compare_greenhouse.jpg)

### Python

`kohakumoss.inference.MossPipeline.from_pretrained(weights_directory, adapters=[(checkpoint, 1.0)])` を使用します。チュートリアルのステップ 6 を参照してください。

## ライセンスと注意事項

- MOSS-Image：Apache-2.0。KohakuMoss：KohakuMoss License 1.0。
- サンプル画像は Codex（gpt-image-2）で参照画像から生成しました。人物は架空で、素材は学習・研究用です。服装や場面は『ハリー・ポッター』を思わせる英国の寄宿学校風です。サンプル素材を商用利用しないでください。
- 既知の課題：サンプルデータの 79% が制服姿で、左向きの角度が少なくなっています。Moss の画像のみを使い、正則化画像を使わない基本的な学習方法です。LoRA を読み込むと、プロンプトで指定していない外見、人種、見た目の年齢が Moss に寄り、`moss01` の有無による差は小さくなります。今回のテストでは、明示的に指定した髪色、目の色、性別は影響を受けませんでした。この LoRA は Moss を生成したいときに読み込んでください。`moss01_leak_compare` ワークフローで挙動を確認できます。
