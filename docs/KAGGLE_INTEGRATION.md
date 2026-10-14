# Kaggle Notebook 集成

## 官方来源

- [比赛](https://www.kaggle.com/competitions/gemma-4-developer-agent)
- [规则](https://www.kaggle.com/competitions/gemma-4-developer-agent/rules)
- [Getting Started](https://www.kaggle.com/code/ryanholbrook/getting-started-gemma-4-developer-agent)，本实现读取版本 3。
- 官方依赖数据集：`metric/gemma-4-developer-agent-wheelhouse`。
- 比赛数据：`/kaggle/input/competitions/gemma-4-developer-agent`；包含 `tasks.jsonl`、`snapshots`、`graphs`、`embeddings`、`wheels` 和 `sample_submission`。
- 模型：`/kaggle/input/models/google/gemma-4/other/gemma-4-31b-it-qat-w4a16-ct/2`。

Notebook 代码已按 Python 语法解析检查，但尚未在 Kaggle 执行。官方比赛数据需要账户权限、身份验证与规则接受；这些操作必须由参赛者本人完成。

## 操作步骤

1. 登录 Kaggle，阅读并接受完整比赛规则，检查账号身份验证和 GPU 配额。下载/阅读 `HARNESS_README.md` 和完整 `sample_submission`，核对目前的工具与 YAML 合约。当前云环境未能下载这两项；不要把本文视为规则已审核的证明。
2. 在本仓库运行 `scripts/setup.sh` 与 `scripts/build_zip.sh`。将生成的 `submission.zip` 上传为自己的 Notebook 数据集，例：`v0-coding-agent`。
3. 将 `notebooks/v0_official.ipynb` 导入 Kaggle，或 fork 官方 Getting Started Notebook 并按此集成版本修改。附加比赛数据、官方 wheelhouse 和指定 31B 模型。将 ZIP_PATH 调整为自己数据集的实际路径。
4. 使用适合 31B 模型的 GPU 环境；官方 Notebook 自动按可见 GPU 数量选 tensor parallel 1/2/4。GPU 内存不足是运行阻塞，不能偷偷改成另一模型。Internet 关闭；依赖由官方 wheelhouse 离线安装。不要使用本仓库 CPU 开发环境的 Transformers 版本启动 Gemma 4。
5. 按顺序运行：环境初始化→解压自己的 V0 包→读取官方 README/sample→图数据检查→启动 vLLM→官方编译器验证→一个公开任务的 Phase 1 推理和 Phase 2 验证→官方打包检查。
6. 确认声明模型恰好是 31B、`adapter_map` 为空、没有子 Agent。vLLM 必须使用 `tool_call_parser='gemma4'`、`reasoning_parser='gemma4'`、`enable_auto_tool_choice=True`。模型注册由 `server_instance.create_model_registry` 完成；不调用远程模型。
7. 检查真实结果中的 `resolved`、`test_exit_code`、`tool_calls`、`duration_seconds`、`patch_chars`，并查看 Harness 轨迹，确认按流程执行和调用了 `submit_patch()`。保存 `/kaggle/working/v0_public_results.json`、Harness results 和 vLLM 日志。仅有非空 patch 或成功启动不足以证明任务通过。
8. 从 Notebook 输出下载新生成的 `submission.zip`。只有规则合规、真实评测完成后才提交比赛。公开任务结果并非排行榜分数。不要提交 Notebook 中用于观察 patch 的 CSV 代替 ZIP。

## 最小工具与流程

工具名直接来自官方 `swegemma.tools.create_tools`：`get_status`、`run_command`、`read_file`、`edit_file`、`write_file`、`submit_patch`。未使用可选图检索工具。

`run_command(command=...)` 支持定位、测试和 Git Diff；`edit_file(filepath, old_string, new_string, allow_multiple=False)` 定点替换。最终 `submit_patch()` 无参数，捕获工作树相对 baseline 的 diff。测试失败不能伪报成功。Harness 会过滤受保护测试文件，应修复实现而非改动受保护测试。

`eval_config.yaml` 使用官方 Notebook 的默认 300 秒命令/验证超时、100 次工具调用、60 分钟任务预算。正式限制仍由比赛 Harness 控制，不能用本地配置绕过。

## 开发依赖与正式依赖的区别

`scripts/setup.sh` 从官方数据集下载五个已核对 SHA-256 的 wheel，并安装可通过 `pip check` 的 CPU 开发依赖。SHA-256 是此次官方 HTTPS 下载的固定摘要，不是声称官方发布了签名清单。上游内容变化时脚本会拒绝安装，需要重新审核来源。

开发环境的 CPU Torch 和 Transformers 4.57.6 用于接口测试与依赖一致性，不支持在这里验证 Gemma 4 推理。Kaggle 集成 Notebook 保留官方离线 wheelhouse 安装流程，使用其 Transformers 5.13.1 及 GPU 运行依赖。不要混用两套环境。
