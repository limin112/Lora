// 第一次在这个浏览器里打开 ComfyUI 时（还没有保存过任何工作流草稿），或者画布是空的，
// 自动打开 moss01 的「原模型 vs 加 LoRA」对比工作流，代替 ComfyUI 自带的默认工作流。
// 之前打开过的浏览器会恢复用户上次的工作流，不会被替换。
import { app } from "../../scripts/app.js";

const TEMPLATE = "api/workflow_templates/moss01_lora/moss01_leak_compare.json";
const TAB_NAME = "moss01_原模型vsLoRA对比";

async function openMoss01(firstVisit) {
  // 前端在扩展初始化之后才载入工作流：最多等 10 秒，等画布上出现节点
  for (let i = 0; i < 40 && !app.graph?._nodes?.length; i++) {
    await new Promise((r) => setTimeout(r, 250));
  }
  await new Promise((r) => setTimeout(r, 500));
  if (!firstVisit && app.graph?._nodes?.length) return;
  const res = await fetch(TEMPLATE);
  if (!res.ok) return;
  await app.loadGraphData(await res.json(), true, true, TAB_NAME);
  // 第一次打开时，ComfyUI 自带的默认工作流在另一个标签页里，顺手关掉，只留我们的
  const ws = app.extensionManager?.workflow;
  if (firstVisit && ws) {
    for (const w of [...ws.openWorkflows]) {
      if (w !== ws.activeWorkflow && w.isTemporary) await ws.closeWorkflow(w);
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
