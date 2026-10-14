# 第二阶段实际执行记录

日期：2026-10-14。目标：一道真实公开任务的指定 Gemma 4 推理与 Phase 2。

## 检出与接口复核

- 本轮起点：本地 `feat/v0-coding-agent` HEAD `24bfbc64e1b78f64d3d54c46fb3a8f596b7093f9`；Git 原生读与 GitHub PR API 确认远端 PR #1 head 完全相同。PR 仍为 Draft，base 为 main。工作树开始时干净。
- 成功通过公开 API 读取官方 Getting Started，仍为版本3；没有调用受保护比赛数据 API，也没有寻找比赛数据副本。之前的401按账号授权处理。
- 当前 KAGGLE_API_TOKEN / KAGGLE_USERNAME / KAGGLE_KEY 均未注入；只检查变量是否存在，没有打印值。没有 nvidia-smi。当前机器不能启动真实 Kaggle GPU 测试。
- 核对已下载官方 wheel：swegemma 0.2.11、adk_submission 0.2.13、adk_eval_core 0.1.0、google-adk 1.36.1、google-genai 2.11.0。
- 实际阅读 `Evaluator.evaluate_task(context=...)`、原生 per-task 日志、`SessionTrace.save(format=...)`、`verify_task`、`VllmServer.start/stop/log_path`、`EvaluationBudget` 实现。发现服务 stop 会删除临时日志，已在 stop 前复制；start 失败则保存异常 output。
- 60分钟只覆盖Agent预算；Phase2测试300秒并不包含全部环境准备。新增外层墙钟和总会话接纳检查。

## 完成的实现

- Notebook 自包含，自动定位官方竞赛输入/wheelhouse/模型与自己的ZIP，兼容新旧挂载布局；缺失/歧义输入直接报告。无下载或授权绕过。
- 固定31B、无LoRA/子Agent、只用六个官方工具；去掉首次任务不需要的图检索演示。
- 一次运行一个独立证据目录，捕获安装、GPU、vLLM、Harness、模型与工具事件、Patch、Phase2输出、官方resolved与异常。结果不写入提交包。
- 单题60分钟Phase1、75分钟外层；批量8分钟Phase1/12分钟外层，串行最多50题，规划660分钟，并设705分钟软截止与15分钟退出余量。底层同步操作取消不保证硬实时。
- `first_task_goal_completed` 只标记真实推理/显式提交/Phase2执行证据；修复成功与否另取官方resolved，比赛分数始终为空。

## 实际测试

本轮可执行检查日志：`docs/validation/stage2/check.log`。

- 本地17项unittest通过：原6项，加11项挂载/ZIP/预算/官方API/Notebook同步/证据缺失判定/Trace恢复/超时与返回值保存测试。
- 真实官方 `compile_submission` 通过；原工具合成修复集成通过。没有Gemma推理。
- Notebook所有代码单元按支持top-level await的Python编译规则检查；执行计数与outputs保持为空。测试确认Notebook与其生成源码一致。
- `pip check`通过。提交ZIP与上一阶段内容一致，不把CPU开发环境或控制代码打入Agent包。
- 测试中第一次误用 `SessionTrace.record_custom` 的工具字段，按真实ADK Event格式纠正fixture后重跑通过；这不代表运行过真实模型。

## 未执行与外部阻塞

**唯一核心目标仍未达成：真实公开任务的Gemma4推理和Phase2尚未执行。**

需要参赛账号在Kaggle挂载受授权的官方比赛输入、wheelhouse、指定31B模型与ZIP，并执行Notebook。完整规则、HARNESS_README、sample仍需账号侧阅读核对。此处不声称任何公开任务通过、模型修复成绩或排行榜分数，未用Codex或模拟返回值替代正式评测。

运行后应保存并审查run ZIP里的manifest、packages、模型路由、Trace、显式submit_patch、最终Patch、Phase2日志和result，再根据真实失败继续修复。具体操作见 `KAGGLE_INTEGRATION.md`。
