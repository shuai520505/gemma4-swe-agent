# Kaggle 官方环境首次单题实测

当前目标是保存一道**真实公开任务**的 Gemma 4 推理与 Phase 2 验证证据。当前仓库尚无此类真实结果；本地测试不提供修复分数。

## Kaggle 操作步骤

1. 在自己的 Kaggle 账号登录并加入[比赛](https://www.kaggle.com/competitions/gemma-4-developer-agent)，完成所需身份验证，阅读/接受[规则](https://www.kaggle.com/competitions/gemma-4-developer-agent/rules)。比赛下载 API 的 **401 是账号授权问题**。本 Notebook 不调用该 API，也不会寻找数据副本或绕过授权。
2. 导入 PR #1 的 `notebooks/v0_official.ipynb`，或 fork [官方 Getting Started](https://www.kaggle.com/code/ryanholbrook/getting-started-gemma-4-developer-agent)。本 Notebook 接口核对版本为官方 v3，使用其官方 wheelhouse 安装方式和 Evaluator。
3. 用 Kaggle **Add Input** 挂载四项输入：

   | 输入 | 选择 |
   | --- | --- |
   | 官方比赛数据 | `gemma-4-developer-agent`，含 tasks、snapshots、wheels、graphs、embeddings、HARNESS_README 和 sample_submission |
   | 官方依赖数据集 | `metric/gemma-4-developer-agent-wheelhouse` |
   | 指定模型 | `google/gemma-4/Other/gemma-4-31b-it-qat-w4a16-ct/2` |
   | 自己的 V0 包 | 将本仓库根目录 `submission.zip` 上传为自己的数据集，然后挂载 |

4. 选择能加载 31B 的 GPU 环境，优先与官方 4×L4 配置一致；关闭 Internet。Notebook 从文件签名自动发现新/旧挂载布局和 ZIP 数据集名称，无需改 slug。遇到重复挂载时移除重复项，或设置 `INPUT_PATHS`。GPU 不可用或内存不足会直接报告，不切换模型。
5. 保持 `RUN_MODE='single'`、`TASK_INSTANCE_ID=None`。逐个执行单元 1–6。默认选官方任务列表第一题；需要复现指定公开题时填其 instance_id。单元 2 会保存官方 README 和 sample YAML，执行前阅读它们，核对规则。所有 Agent 工具都来自官方注册表；V0 无 LoRA、子 Agent、图检索演示或自定义工具。
6. 等待本地 vLLM 启动和编译，随后运行真实 `Evaluator.evaluate_task`。它依次执行 Gemma Phase 1 与官方 Phase 2。运行期间查看 Notebook 输出、`live_status.json` 和官方 `harness/logs`。不把服务成功启动或编译通过当作任务修复成功。
7. 完成或失败后，从 Notebook **Output** 下载 `/kaggle/working/v0_runs/<run-id>.zip`。同时保留 Kaggle 的完整执行日志。核对下面的证据。如果中断在模型启动/安装阶段，下载该阶段产生的 Diagnostics ZIP。若直接关闭整个内核，已落盘文件仍可检查，但无法保证最终 ZIP 创建。
8. 首次目标仅在有真实模型调用、成功的显式 `submit_patch()`、非空 Patch 和 Phase 2 实际测试输出时记为 `first_task_goal_completed=true`。修复是否成功仍以官方 `resolved` 和验证输出判断；两阶段执行完成可以是 `resolved=false`。不要将其转换为排行榜成绩。

无需将 GitHub 仓库或开发脚本作为额外 Kaggle 输入；辅助控制代码已嵌入 Notebook。更改辅助函数后，开发者运行 `python scripts/build_kaggle_notebook.py` 生成 Notebook。

## 证据文件与异常诊断

每次执行建立新的 UTC run-id 目录，不覆盖上次证据。

| 文件 | 内容/用途 |
| --- | --- |
| `manifest.json`、`packages.json` | 实际挂载路径、ZIP SHA-256、预算、官方依赖版本、指定模型 |
| `gpu.txt`、`vllm_config.json`、`served_models.json` | GPU、实际服务配置与本地 `/v1/models` 返回；不包含 API key |
| `installation.log`、`vllm.log`、`harness.log` | 离线安装、模型加载和 Harness 异常 |
| `harness/logs/<instance-id>.log` | Harness 原生边运行边落盘的 ADK 输出与工具记录 |
| `tasks/001/live_status.json` | 周期保存阶段、模型调用次数、工具调用次数和提交状态 |
| `tasks/001/agent.patch`、`last_submitted.patch` | 最终 Patch；被取消时保留当时已经提交的 Patch |
| `tasks/001/trace.json`、`trace_legacy.json` | 官方 SessionTrace 的 ATIF 与原始事件格式 |
| `tasks/001/model_events.jsonl`、`tool_events.jsonl` | 从原生 Trace 提取的模型输出/usage/提示词事件，及工具参数/返回值 |
| `tasks/001/phase2.log`、`result.json` | 验证 stdout/stderr、退出码、resolved、错误、显式提交证据 |
| `exception.json`、`run_status.json`、`budget_stop.json` | 阶段、异常与堆栈、完成状态、预算停止后未运行的题目 |

`model_events.jsonl` 保存的是官方 ADK Trace 事件，不是原始 HTTP 逐次请求抓包；`total_llm_calls` 直接取 Harness 计数。日志不导出环境变量或凭据，不打印/传入 gold patch。vLLM 临时日志在停止服务前复制；启动失败时保存官方异常附带的 captured output。

先检查 `exception.json.stage`：

- `inputs`：挂载缺失/重复、比赛权限、错误模型或 ZIP 内容。通过账号授权与 Add Input 解决。
- `gpu_or_installation`：GPU、离线 wheel 或二进制依赖错误。检查 `gpu.txt` 与 `installation.log`，不要安装非官方替代工具。
- `harness_preflight`：官方 API 版本、任务快照、YAML/工具不匹配。官方包升级时停止并重新核对，不猜测接口。
- `vllm_startup_or_compile`：检查 `vllm_startup_failure.log`/`vllm.log`，常见原因是 OOM、CUDA、模型路径或解析器。仍使用指定 31B。
- `evaluation`：进一步查看任务目录异常、原生日志和 Phase 2 输出。空测试规格、快照/依赖安装失败、模型/工具错误、超时与修复失败要分别记录。没有 Phase 2 输出不能按退出码默认值判定通过。

## 预算与 12 小时批量配置

官方 `max_time_minutes=60` 是 **Phase 1 Agent 会话预算**；安装、模型启动、快照/环境准备和 Phase 2 都还有开销。直接按 12×60 分钟安排 12 题不成立。`verification_timeout_seconds=300` 只限制 Phase 2 的测试命令，不限制全部准备过程。

| 模式 | Phase 1/题 | 工具次数 | 单命令 | Phase 2 测试 | 外层墙钟/题 | 最多题数 |
| --- | --- | --- | --- | --- | --- | --- |
| 首次单题 `single` | 60 分钟 | 100 | 300 秒 | 300 秒 | 75 分钟 | 1 |
| 后续批量 `batch` | 8 分钟 | 60 | 120 秒 | 300 秒 | 12 分钟 | 50，串行 |

先完成单题，再选择 batch。50×12+安装/模型启动预留45+打包退出预留15=660分钟，规划为 **11小时**，低于12小时。安装实际时间可能超过预留；因此 Notebook 从安装前计时，到705分钟软截止不再接纳一个放不下的完整任务，记录未执行任务并留15分钟退出。

外层超时包含任务环境准备、Phase 1 和 Phase 2；超时则保存异常、原生日志及已提交 Patch，取消当前评测。同步子进程/线程可能延迟响应取消，这不是硬实时保证；必要时在 Kaggle 停止运行，平台的12小时限制仍是最终硬上限。不能声称一定完成50题。每题结束立即保存，第一次缺失核心证据时停止批量扩大并先诊断。

该 profile 仅用于公开本地实测，不修改上传 ZIP 的60分钟默认配置，也不改变官方评分预算。

## 已验证与尚未验证

本地：官方沙箱编译、工具集成、路径发现、证据保存、取消诊断、预算控制与 Notebook 可执行语法检查。Fixture/模拟返回值测试仅验证控制逻辑，不算真实任务结果。

尚未执行：Kaggle GPU 上的31B加载、Gemma模型调用、至少一道真实公开任务与Phase 2。当前 Codex 机器无 Kaggle 授权凭据、无 GPU/权重；需要参赛者在其授权账号运行本 Notebook 并保存上述证据。当前没有任何修复分数。
