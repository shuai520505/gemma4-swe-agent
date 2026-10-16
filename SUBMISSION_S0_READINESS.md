# S0 首次提交就绪记录

候选由 V0 独立派生，原 V0/V1 源码、ZIP 与证据未修改。保留 31B v2、六工具、单 Agent 和原始 V0 Prompt；不包含 Harness 控制器、测试日志、参考答案、LoRA 或其他模型。

## 冻结文件

- ZIP：`candidates/s0/submission.zip`，1908 字节，SHA-256 `3303d6e1dd246d3861910701beb580c8d9a165ea1eb1c1a13d8c8ba9d6efd4f9`。
- Notebook：`candidates/s0/notebook/submission.ipynb`，SHA-256 `eb332622560d93d074cf4ad57ee5572c42c87fbd195eeefe9772a202cd41498a`。
- agent.yaml：`9f3631984cb80bf1dadc4758adb2edf2cb1cb38474ebb35908ae6b49207eb7ad`。
- 原 V0 Prompt：`5f43c3a546c4c21765aff5e09a92126b1bb104b6e8423b269364a0b8f286a7ce`。
- eval_config.yaml：`4336195f5a2c63071dd2ee2448d13f6630c4a9f81ba4afc399dedb8312785861`。

ZIP 根目录只有 agent.yaml、eval_config.yaml、prompts/system.md。Notebook 只解码已冻结 ZIP、验证布局与哈希、写出 /kaggle/working/submission.zip；不装包、不加载模型、不重复开发评测。

## 初始预算及 12 小时风险

每题 Agent 5 分钟，最多 60 次计费工具，单命令 120 秒（原生工具还受剩余会话时间限制）。此为初始探分候选，不是经调参验证的最优值。验证阶段由官方评分器控制，不额外写入非公开评分参数。

官方总 Agent 上限 12 小时，包含 Sandbox 初始化、不包含 Patch 验证。保守规划示例为总启动/收尾预留 60 分钟，剩余时间满足：`N × (300 秒 + 每题初始化/抽取开销) <= 39600 秒`。60 分钟是规划假设，不是官方保证。

| 假设隐藏任务数 N | 每题可容纳的平均额外开销 |
| --- | --- |
| 100 | 96 秒 |
| 120 | 30 秒 |
| 129 | 约 7 秒 |

公开数据集有 129 题，但不能据此断言隐藏题数。r12 subprocess 开发记录中每题准备约 13 秒，其中包含工作进程导入；生产 Docker 准备并未测量，不能直接代入保证全量完成。长 Issue、模型输出预留、60 工具限制和 5 分钟截止都可能降低修复率。S0 没有附加本地 RequestGuard；官方评分环境负责上下文与全局截止。

## 已执行检查

- 官方 Kaggle Linux 编译：通过，模型 `openai/gemma-4-31b-it-qat-w4a16-ct`，六工具、0 子 Agent；原 V0 Prompt 字节一致。
- 现有静态测试：5/5 通过，原始日志 `docs/validation/s0/official-static-tests.log`。
- 实际包版本：swegemma 0.2.11、adk-submission 0.2.13、google-adk 1.36.1、LiteLLM 1.82.4、vLLM 0.19.1；全量 wheel 字节哈希单独保存。
- 保存的包装 Notebook v1：COMPLETE；实际生成 submission.zip（1908 字节），CRC 正确、根目录 agent.yaml 存在，哈希与冻结候选一致。
- 上述 CPU 检查未生成 Gemma 回复，不代表任务修复成功。

## 正式提交步骤和状态

已授权尝试提交保存版本：`kaggle competitions submit gemma-4-developer-agent -k wudangdexiaodoashi/gemma4-s0-first-submission -v 1 -f submission.zip -m "S0 V0 prompt 5min 60tools initial probe"`。

提交前确认官方编译及保存版输出完成；提交响应、Submission ID、状态、Public Score 和运行错误只根据官方返回另存。该命令已执行并由官方接纳：Submission ID **57261002**，提交时间 2026-10-16 16:04:50（UTC+8），保存版本 v1。官方 API 在 16:09:27（UTC+8）返回 PENDING，Public Score 为 null，error_description 为空；尚未取得终态，空错误不代表运行已成功。原始记录在 `docs/validation/s0/submission-57261002-initial.json`。若 CLI 受限，可打开保存版本 Notebook，在 Output 核对 submission.zip 后选择 Submit to Competition；不能提交只编辑未保存运行的版本。

官方依据：[评估说明](https://www.kaggle.com/competitions/gemma-4-developer-agent/overview)、[工作人员说明保存版本输出](https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/743683)。

## 本次交付时官方状态

截至 2026-10-16 20:19:23（UTC+8），Submission **57261002** 仍为 **SubmissionStatus.PENDING**，Public Score **未返回（null）**，官方 error_description 为空。尚不能确认评分运行成功或失败，不能把排队状态记成0分。最新原始API快照见 `docs/validation/s0/submission-57261002-latest.json`。本次只提交一次，没有取消、重复提交或消耗另一版本探分。
