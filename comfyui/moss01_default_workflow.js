// 打开 ComfyUI 时，如果画布上是 ComfyUI 自带的默认工作流（或者是空的），
// 自动换成 moss01 的「原模型 vs 加 LoRA」对比工作流。用户自己搭的工作流不会被替换。
import { app } from "../../scripts/app.js";

const TEMPLATE = "api/workflow_templates/moss01_lora/moss01_leak_compare.json";
const TAB_NAME = "moss01_原模型vsLoRA对比";
// ComfyUI 自带默认工作流里的节点（旧版是 SD1.5 示例，新版是 Z-Image 示例）
const STOCK_TYPES = new Set(["CheckpointLoaderSimple", "UNETLoader", "ModelSamplingAuraFlow", "CLIPLoader",
  "CLIPTextEncode", "EmptyLatentImage", "EmptySD3LatentImage", "KSampler", "VAELoader", "VAEDecode", "SaveImage"]);

function isStockDefault(graph) {
  const nodes = graph?._nodes ?? [];
  return nodes.length === 0 || (nodes.length <= 12 && nodes.every((n) => STOCK_TYPES.has(n.type)));
}

async function openMoss01(firstVisit) {
  // 前端在扩展初始化之后才载入工作流：最多等 10 秒，等画布上出现节点
  for (let i = 0; i < 40 && !app.graph?._nodes?.length; i++) {
    await new Promise((r) => setTimeout(r, 250));
  }
  await new Promise((r) => setTimeout(r, 500));
  if (!firstVisit && !isStockDefault(app.graph)) return;
  const res = await fetch(TEMPLATE);
  if (!res.ok) return;
  const data = await res.json();
  const ws = app.extensionManager?.workflow;
  const replaced = ws?.activeWorkflow;
  if (!firstVisit && ws?.openWorkflows.some((w) => w.filename === TAB_NAME)) {
    // 已经开着一个我们的标签页：就在当前标签页里原地替换，不再多开一个
    await app.loadGraphData(data, true, true, replaced);
    return;
  }
  await app.loadGraphData(data, true, true, TAB_NAME);
  // 被换掉的默认工作流还留在另一个标签页里，关掉它（第一次打开时把其他临时标签页也关掉），只留我们的
  if (ws) {
    for (const w of [...ws.openWorkflows]) {
      if (w !== ws.activeWorkflow && w.isTemporary && (firstVisit || w === replaced)) await ws.closeWorkflow(w);
    }
  }
}

app.registerExtension({
  name: "moss01.defaultWorkflow",
  setup() {
    if (new URLSearchParams(location.search).has("template")) return; // 网址里指定了模板，就不管
    // 这时前端还没写入草稿：没有任何草稿记录，说明是第一次打开
    const firstVisit = !Object.keys(localStorage).some((k) => k.startsWith("Comfy.Workflow.Draft") || k === "workflow");
    openMoss01(firstVisit); // 不 await：初始化阶段不能等，否则会卡住 ComfyUI 启动
  },
});
