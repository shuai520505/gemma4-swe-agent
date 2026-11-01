# R12 GPU 实验最终报告

**结果：唯一一次派发被拒绝，真实会话完成 0/9。当前为 R12_INTEGRATION_BLOCKED。**

Kaggle `SaveKernel` 返回 HTTP 400 / INVALID_ARGUMENT：`The kernel source must be less than 1 megabytes in size.` 实际 Notebook 文件 1053448 字节，代码单元 UTF-8 合计 1052862 字节，超过 1 MiB（1048576 字节）。我在派发前漏查源码大小，这是执行包装错误，不是 Gemma 决策、编辑工具或 GPU 容量失败。

只发送 **1 次 SaveKernel**，返回失败后 **0 次重试**；没有得到 Notebook 版本、GPU 观测、vLLM 启动或真实模型请求。状态 API 后续查询不可访问，记为 UNKNOWN，未将它伪造成平台 COMPLETE/已完成清理。权威拒绝响应、请求回执及配额快照均保留。没有第二次派发、正式比赛提交、候选修改、换题、换序或 R3。

派发前已核对远端 PR #44 HEAD 为 b6492e5，本地 Manifest/RESOURCE_READINESS/Coordinator 与远端一致；Kaggle 认证有效。扣除 Reservations 后可用配额 30.0000 小时，满足原 73200 秒门槛。事后 API 显示 used=0.0 秒、reserved=0.0 秒，观测到配额消耗变化 0.0 秒。GPU 型号和八个模型文件的本次 GPU 运行校验均未发生，不能拿历史 CPU 校验冒充。

原始 Manifest 和 RESOURCE_READINESS 未修改，三个候选原始哈希保持一致；一次性 READY 运行 Manifest 未创建。授权包装层已实现真实四 L4/CUDA 检查和原清单/授权哈希绑定，但 Notebook 未运行，所以这些检查仅有明确标注的 CPU mock 单元测试，没有实际 GPU 分配 PASS。

| 必答问题 | 实际结论 |
|---|---|
| 1. 九次实际完成多少？ | 0/9，全部 NOT_RUN；没有会话启动。 |
| 2. 三候选各成功多少？ | 三者均执行 0 次、VALIDATED_REPAIR 计数 0；成功率为 null，不是 0/3。 |
| 3. R1 是否减少缺参数编辑？ | UNKNOWN；没有真实工具调用数据。 |
| 4. R2 是否改善首次生产修改时间？ | UNKNOWN；没有真实编辑事件。 |
| 5. R2 是否增加有效提交率？ | UNKNOWN；没有真实提交或 Patch。 |
| 6. 哪个真实成功率最高？ | 无法比较。 |
| 7. 哪些来自工具、哪些来自模型决策？ | 本次只有派发包装的基础设施错误；没有模型决策或编辑工具失败样本。 |
| 8. Token、工具、耗时是多少？ | 会话 Token usage、工具次数、Agent 耗时均无观测值，保留 null；真实 Gemma 请求数 0。派发尝试 1 次，观测 GPU 配额变化 0 秒。 |
| 9. 有候选造成修复回归吗？ | 未评估，不能宣称无回归。 |
| 10. 是否足够建议 R3？ | 否；没有新的修复证据，R3 未构建且仍被禁止。 |

九次原始轨迹、HTTP 模型日志、ADK 调用、Diff、提交/超时 Patch、可信测试和独立语义审查在证据索引中均明确为 NOT_RUN，没有制造空轨迹冒充执行证据，也未挪用 CPU 合成补丁作为修复结果。

作为可审查的包装修正，已准备 **40831 字节**的精简 Notebook：复用已挂载、SHA 固定的 CPU 源码 ZIP，避免重复内嵌 base64 源码。仅通过语法和大小静态检查；文件首行强制拒绝执行，标注 PREPARED_ONLY_NOT_AUTHORIZED，未派发。实际失败 Notebook、BUILD 和原始回执保持原样。派发脚本已补大小预检，但本次授权不允许再次运行派发。

原计划仍为四 L4、18000 秒、九次各 480 秒 / 28 计费工具 / 80 turns / 240 秒命令超时，预期 3–4 quota-hours、上限 10 quota-hours。本次没有进入该执行阶段。按你“不得重试”的限制，本次实验到此停止。
