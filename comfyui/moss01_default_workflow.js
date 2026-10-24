// 让 ComfyUI 的「默认工作流」变成 moss01 的「原模型 vs 加 LoRA」对比工作流：
// 打开页面时，以及之后任何时候当前标签页变成 ComfyUI 自带的默认工作流（比如关掉最后一个标签页时它会自动新开一个），
// 都换成对比工作流。空白画布和用户保存过的工作流不会被替换。
import { app } from "../../scripts/app.js";

const TEMPLATE = "api/workflow_templates/moss01_lora/moss01_leak_compare.json";
const TAB_NAME = "moss01_原模型vsLoRA对比";
// ComfyUI 自带默认工作流里的节点（旧版是 SD1.5 示例，新版是 Z-Image 示例）
const STOCK_TYPES = new Set(["CheckpointLoaderSimple", "UNETLoader", "ModelSamplingAuraFlow", "CLIPLoader",
  "CLIPTextEncode", "EmptyLatentImage", "EmptySD3LatentImage", "KSampler", "VAELoader", "VAEDecode", "SaveImage"]);

function isStockDefault(graph) {
  const nodes = graph?._nodes ?? [];
  return nodes.length > 0 && nodes.length <= 12 && nodes.every((n) => STOCK_TYPES.has(n.type));
}

let busy = false;

async function ensureMoss01(firstVisit = false) {
  if (busy) return;
  busy = true;
  try {
    const ws = app.extensionManager?.workflow;
    const current = ws?.activeWorkflow;
    const empty = !app.graph?._nodes?.length;
    if (!(isStockDefault(app.graph) || (firstVisit && empty))) return;
    if (current && !current.isTemporary) return; // 用户保存过的工作流不动
    const res = await fetch(TEMPLATE);
    if (!res.ok) return;
    const data = await res.json();
    if (current && ws.openWorkflows.some((w) => w !== current && w.filename === TAB_NAME)) {
      await app.loadGraphData(data, true, true, current); // 已经开着一个我们的标签页：原地替换，不再多开
      return;
    }
    await app.loadGraphData(data, true, true, TAB_NAME);
    // 被换掉的默认工作流还留在另一个标签页里，关掉它（第一次打开时把其他临时标签页也关掉），只留我们的
    if (ws) {
      for (const w of [...ws.openWorkflows]) {
        if (w !== ws.activeWorkflow && w.isTemporary && (firstVisit || w === current)) await ws.closeWorkflow(w);
      }
    }
  } catch (e) {
    console.warn("[moss01] 打开对比工作流失败", e);
  } finally {
    busy = false;
  }
}

app.registerExtension({
  name: "moss01.defaultWorkflow",
  setup() {
    if (new URLSearchParams(location.search).has("template")) return; // 网址里指定了模板，就不管
    // 这时前端还没写入草稿：没有任何草稿记录，说明是第一次打开
    const firstVisit = !Object.keys(localStorage).some((k) => k.startsWith("Comfy.Workflow.Draft") || k === "workflow");
    (async () => {
      // 前端在扩展初始化之后才载入工作流：最多等 10 秒，等画布上出现节点
      for (let i = 0; i < 40 && !app.graph?._nodes?.length; i++) {
        await new Promise((r) => setTimeout(r, 250));
      }
      await new Promise((r) => setTimeout(r, 500));
      await ensureMoss01(firstVisit);
      setInterval(() => ensureMoss01(), 1500); // 之后每 1.5 秒看一次
    })(); // 不 await：初始化阶段不能等，否则会卡住 ComfyUI 启动
  },
});
