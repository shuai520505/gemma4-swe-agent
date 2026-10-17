# S1 独立优化计划

起点为远程 `feat/v0-coding-agent` 的 `972d1dd940db3910dd78685d6e37152e96ab514b`；另建 `feat/s1-score-optimization` 与独立工作目录。远程 main 为 `0b0909df0177affa1eafe92bac679199235e4fd9`，CURE 分支为 `017a32dce10c6a1265ad225043092c948d8c7337`。本轮只新增 s1/ 文件。CURE Prompt、状态、选择器、研究控制器均不导入、不打包。

已阅读 NEXT_EXPERIMENTS、RESEARCH_REVIEW、PUBLIC_SOLUTIONS、SUBMISSION_S0_READINESS、HARNESS_V2_DESIGN、formal-paired-01/REPORT、S0 配置和官方源码。本轮不重复文献研究。

## 分数锚点与证据边界

授权 CLI 本轮重新查询：S0 submission 57261002，COMPLETE，Public Score **0.13**。只有这个分数来自正式评分。S0 ZIP SHA 为 `3303d6e1dd246d3861910701beb580c8d9a165ea1eb1c1a13d8c8ba9d6efd4f9`；原文件含 null/PENDING 的历史记录继续保留，不覆盖。新的观察单独保存。

现有 Trace 支持以下开发任务现象：formal-paired-01 中 HTTPX/V1 480 秒后空 Patch，Rich/V1 与 FastAPI/V0 达到 Agent 截止但取得真实失败 Phase2，六个非空 Patch 均可应用且仍有行为断言失败；首题 FastAPI 15661 的实现入口与评估导入路径不一致。它们支持调查预算与接口遗漏假设，不能说明 S0 隐藏评分每道失分的原因。未取得 S0 隐藏任务逐题 Trace，不能估计这些瓶颈在 0.13 中的占比。

16384 输出预留是已核验配置事实；它**可能**引起过早上下文拒绝/压缩，不是已证实的主要失分原因。公开 v19 的 0.17 是作者报告，不是本项目复现结果。

## 顺序与单因素

| 实验 | 对照 | 唯一变化 | 当前许可 |
| --- | --- | --- | --- |
| E1 | control | 输出 16384 → 8192 | CPU 后一个新公开题 smoke；门禁通过后最多四个新开发题 |
| E2 | control，或另行冻结的 E1 配置基线 | thinking 4096 → 0 | 完整 Runner CPU；GPU 尚未登记，512 仅语义测试 |
| E3 | control | 追加有界定位短段 | 完整 Runner CPU；GPU 尚未登记 |
| E4 | control | 追加风险定向验证短段 | 完整 Runner CPU；GPU 尚未登记 |

E1 保持原 S0 Prompt、31B、六工具、单 Agent、5 分钟/60 工具、thinking4096 与 include_thoughts 默认值。共同固定 seed17，是新的研究条件；不将研究 control 当作正式 S0 重跑，也不把 seed 变化算作 E1 收益。temperature/top_p/top_k 不人为设置，保留官方默认。

E2–E4 都是独立准备，输出仍固定原 16384，不叠加 E1。若将来选择8192作为 E2/E3/E4共同条件，须派生新身份、重新完整 Runner 门禁、冻结新协议，并重新运行该条件对照；不能复用不匹配基线。

## 执行器与可提交边界

`s1-runner-0.1.0` 从 r12 worker 独立派生，精确差异见 diffs/worker-r12.diff。参数化实际 EvalConfig 的时间与工具预算、编译配置核验及请求输出预留；重用冻结 r12 的计数/Issue 保留、增量 ADK 事件、Agent 边界 Patch/Trace、独立 Verifier、进程监督与四态分类。没有修改官方评分 Harness。

研究端 HTTP 观察器、上下文准入与额外证据不进入候选 ZIP，不能宣称它们自动存在于榜单环境。候选仅有 agent.yaml、eval_config.yaml、prompts/system.md，根目录含 agent.yaml；无 Harness、参考 Patch、隐藏测试、日志、LoRA 或子 Agent。

## 升级条件

主终点是完整同预算配对的官方 resolved 净差，且无基础设施/证据门失败。速度、Token 或格式改善只能支持效率结论。四题筛选不提供可靠统计优势；有方向性收益还须独立未用于选择的确认题及打包/总预算核验。未取得这类证据前，保留研究身份，不冻结 S1、不制作宣称提分的正式提交。
