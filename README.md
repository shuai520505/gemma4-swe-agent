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
