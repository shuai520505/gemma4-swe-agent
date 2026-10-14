# Gemma 4 SWE Agent — V0

单一 `gemma-4-31b-it-qat-w4a16-ct` Coding Agent，采用官方 SWE-gemma 工具与沙箱配置编译器。无 LoRA、子 Agent 或自定义评测工具。

```bash
bash scripts/setup.sh
PYTHON_BIN=/workspace/venvs/gemma4/bin/python bash scripts/check.sh
PYTHON_BIN=/workspace/venvs/gemma4/bin/python bash scripts/build_zip.sh
```

`submission.zip` 根目录包含 `agent.yaml`、`eval_config.yaml` 和 `prompts/system.md`。包内没有开发脚本。

已通过官方配置编译与工具链测试，**尚未完成 Gemma 推理或公开任务评测**。静态检查、编译通过不代表比赛得分，也不替代规则审核。

- [Kaggle 集成说明](docs/KAGGLE_INTEGRATION.md)
- [第二阶段验证记录与阻塞项](docs/STAGE2_VALIDATION.md)
- [第一阶段验证记录](docs/VALIDATION.md)
- [可运行的官方 Notebook 集成版本](notebooks/v0_official.ipynb)

CPU 云环境仅用于开发、打包和接口验证。正式推理使用 Kaggle 官方 wheelhouse、模型权重和 Evaluator；不使用 Codex 替代 Gemma。

首次 Kaggle 实测：导入 Notebook，挂载官方比赛数据、官方 wheelhouse、指定31B模型和 submission.zip。默认自动发现路径并跑一题，输出完整证据ZIP；详细操作与12小时批量预算见集成说明。
