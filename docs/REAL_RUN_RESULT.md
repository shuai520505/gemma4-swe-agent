# 指定 31B 真实单题运行结果

2026-10-15（北京时间）。已完成真实推理、显式 Patch 提交和官方 Phase 2 验证调用，**本次没有修复通过**。

| 项目 | 真实观测 |
| --- | --- |
| 分支 / PR | `feat/v0-coding-agent` / [PR #1](https://github.com/shuai520505/gemma4-swe-agent/pull/1) |
| Kaggle Notebook | [Gemma4 V0 Single Public](https://www.kaggle.com/code/wudangdexiaodoashi/gemma4-v0-single-public)，私有，第2版，状态 COMPLETE |
| Run ID | `20261014T161032_870715Z` |
| 模型 | `google/gemma-4/Other/gemma-4-31b-it-qat-w4a16-ct/2`，无 LoRA、无子 Agent |
| GPU | 4× NVIDIA L4，每卡 23034 MiB；tensor parallel = 4 |
| 公开任务 | `fastapi_15661`，`fastapi/fastapi`，base `ee22a4b8ca46dcce26c8c183afc4992a888d8be2` |
| 模型 / 工具调用 | 官方计数26 / 24；原生 Trace 共79条事件，含25次工具调用（其中1次免费 `submit_patch`） |
| 显式提交 | `submit_patch({})` 返回 `status=ok`、`patch_size=4108`、`files_changed=3` |
| Patch | 4108字符；最终 Patch 与 `last_submitted.patch` 字节一致 |
| 任务耗时 | 官方 `duration_seconds=434.587440412`，不含模型安装与启动 |
| 官方结果 | `resolved=false`、`error=null`、`test_exit_code=2` |
| Phase 2 | pytest 已启动，在收集阶段中断；测试正文未执行 |
| 排行榜 | 未提交，无排行榜成绩 |

Phase 2 的真实错误是 `tests/test_prepare_release.py` 无法导入 `scripts.prepare_release`。Gemma 的 Patch 新建了 `scripts/release.py`，另修改版本号和发布说明，未提供验证要求的模块。因此不能把 Notebook COMPLETE 或控制器的 `first_task_goal_completed=true` 当成成功修复。

原始 `result.json` 中的 `phase2_tests_ran=true` 是控制器根据 STDOUT/STDERR 包络判断验证命令已执行。它不能区分测试收集与测试正文。原始文件保持不变；[结果审计](validation/local-kaggle/result-audit.json) 明确记录 `pytest_collection_failed=true`、`test_bodies_executed=false`、`tests_passed=false`。

## 本地完整产物

以下路径相对于仓库根目录，均已实际下载；完整原始文件保留在本机和账号私有 Notebook Output，不打入 Agent 提交 ZIP。

- 完整证据 ZIP：`artifacts/kaggle-single/output-v2/v0_runs/20261014T161032_870715Z.zip`
- 原始运行目录：`artifacts/kaggle-single/output-v2/v0_runs/20261014T161032_870715Z/`
- Patch：该运行目录内 `tasks/001/agent.patch`、`tasks/001/last_submitted.patch`
- 验证与结果：`tasks/001/phase2.log`、`tasks/001/result.json`、`public_results.json`
- 模型与工具：`tasks/001/trace.json`、`trace_legacy.json`、`model_events.jsonl`、`tool_events.jsonl`
- 原生运行日志：`harness/logs/fastapi_15661.log`、`harness.log`、`vllm.log`、`installation.log`
- 完整 Notebook 执行日志：`artifacts/kaggle-single/output-v2/gemma4-v0-single-public.log`
- 本地补充审计：运行目录内 `local-result-audit.json`、`evidence-sha256.txt`

ZIP CRC 检查通过，SHA-256：

```text
b3b6c333eb3a628444798da424923ae3db35ffeaf2c4349a28a75063ec148ba4
```

PR 中的 [结果审计](validation/local-kaggle/result-audit.json) 包含关键产物的字节数和 SHA-256，可与本地文件交叉检查；不发布完整任务输入或验证测试内容。

## 输入与首次失败留存

第1版在输入发现时失败：Kaggle 将上传的 `submission.zip` 自动解包，Notebook 无法找到 ZIP。完整失败输出保留在 `artifacts/kaggle-single/output-v1/`。随后将相同 ZIP 字节保存为 `submission.bundle`，创建私有输入数据集第3版，并为 Notebook 增加这一文件名的发现支持。该兼容修改已完成独立发现/解包检查及 Notebook 语法检查。

实际评测的 PR ZIP / bundle SHA-256：`c9b22eececf11aa65089f1f35ddc629c2ea5824d7d7fc7dfa6a9fcfc006b1c1a`。父目录原有 `submission.zip` 始终保留，其 SHA-256 仍为 `50cc615dd5c457a4233ee6e01bd752e6999490f835d6484b84eacf388c5a43b9`；没有用该旧包替代 PR 分支配置。

实际依赖版本保存在原始 `packages.json`：swegemma 0.2.11、adk-submission 0.2.13、adk-eval-core 0.1.0、google-adk 1.36.1、google-genai 2.11.0、vLLM 0.19.1、torch 2.10.0+cu128、transformers 5.13.1、LiteLLM 1.82.4。实际 `/v1/models` 返回值确认服务模型为指定31B v2。
