# Gemma 4 SWE Agent — V0

单一 `gemma-4-31b-it-qat-w4a16-ct` Coding Agent，采用官方 SWE-gemma 工具与沙箱配置编译器。无 LoRA、子 Agent 或自定义评测工具。

```bash
bash scripts/setup.sh
PYTHON_BIN=/workspace/venvs/gemma4/bin/python bash scripts/check.sh
PYTHON_BIN=/workspace/venvs/gemma4/bin/python bash scripts/build_zip.sh
```

`submission.zip` 根目录包含 `agent.yaml`、`eval_config.yaml` 和 `prompts/system.md`。包内没有开发脚本。

已通过官方配置编译与工具链测试，并在 Kaggle **4×L4** 上完成指定 **31B v2** 的真实公开任务 `fastapi_15661` 推理、显式 Patch 提交和官方 Phase 2 验证调用。**本次修复未通过：`resolved=false`，pytest 在收集阶段因缺少 `scripts.prepare_release` 退出（代码 2），测试正文未执行。**这不是排行榜成绩。

- [Kaggle 集成说明](docs/KAGGLE_INTEGRATION.md)
- [第二阶段验证记录与阻塞项](docs/STAGE2_VALIDATION.md)
- [真实单题结果、日志与 Patch 留存说明](docs/REAL_RUN_RESULT.md)
- [第一阶段验证记录](docs/VALIDATION.md)
- [可运行的官方 Notebook 集成版本](notebooks/v0_official.ipynb)

CPU 云环境仅用于开发、打包和接口验证。正式推理使用 Kaggle 官方 wheelhouse、模型权重和 Evaluator；不使用 Codex 替代 Gemma。

Kaggle 单题实测：导入 Notebook，挂载官方比赛数据、官方 wheelhouse、指定31B模型和 submission.bundle（submission.zip 的原样副本，避免数据集自动解包）。默认自动发现路径并跑一题，输出完整证据ZIP；详细操作与12小时批量预算见集成说明。

已完成首轮逐事件[失败审计](FAILURE_ANALYSIS.md)，并保留不可修改的V0，新增[通用V1候选与设计](V1_DESIGN.md)及[候选ZIP](candidates/v1/submission.zip)。V1只修改提示词，模型、六工具和单Agent保持一致。

2026-10-15已在Kaggle实际执行[预注册配对pilot](experiments/PLAN.md)：计划8次，记录3次后因外层超时停止，剩余5次未执行。唯一完整配对的V0/V1均未解决；V1进入Phase2，98 passed / 1 failed。完整成功率尚不可计算，暂不替换V0；[真实结果](experiments/RESULTS.md)与[本轮审计](experiments/PILOT_01_AUDIT.md)说明上下文溢出、环境接口遗漏及超时证据缺口。所有V0原始文件保持不变。

Harness V2 单独实现上下文准入、分阶段截止、进程隔离及持续证据保存，冻结V0/V1与Pilot 01：[设计与预算](HARNESS_V2_DESIGN.md)、[运行步骤](harness_v2/RUNBOOK.md)、[真实验证记录](harness_v2/VALIDATION.md)、[GPU结果与归因](harness_v2/RESULTS.md)、[正式配对实验草案](harness_v2/FORMAL_EXPERIMENT_DRAFT.md)。CPU门禁已通过；GPU开发任务及正式实验准入以验证记录中的实际证据为准。


## S0、正式配对实验与公开方案研究（2026-10-16）

- 独立首次提交候选：[S0 就绪记录](SUBMISSION_S0_READINESS.md)、[候选ZIP](candidates/s0/submission.zip)、[只输出ZIP的Notebook](candidates/s0/notebook/submission.ipynb)。官方编译及5项既有静态测试通过，保存版本确实生成ZIP。正式Submission ID为57261002；最新API仍PENDING，无官方分数。
- [冻结配对协议](experiments/formal-paired-01/PROTOCOL.md)与[真实执行报告](experiments/formal-paired-01/REPORT.md)：7次执行，6 failed、1 unknown；余下1次按停止规则not_run。完整修复率为null，不判定V1优于V0，不拼接补跑。
- [小模型路线核验](MODEL_ALTERNATIVES_ASSESSMENT.md)：官方支持12B/E4B/E2B，三配置实际编译通过；未做小模型GPU加载、测速或修复验证，31B候选不变。
- [公开榜方案研究](PUBLIC_LEADERBOARD_STUDY.md)：只读分析实际下载的公开源码，记录来源SHA和成绩证据边界；仅提出下一轮消融假设，没有修改冻结候选。
