# CURE V0.1

独立研究版本0.1.0，基于972d1dd，分支 `feat/cure-v01`。原V0/V1/S0、Harness r12、正式实验和证据不变。

- [设计与实现边界](CURE_DESIGN.md)：契约状态、可解释启发式选择器及研究执行器。
- [实际机制结果](MECHANISM_RESULTS.md)：63项官方CPU/API与控制器测试通过、12条脚本重放，包含失败案例。
- [下一步消融草案](ABLATION_PLAN.md)：尚未执行的最小8次GPU机制对照与停止条件。
- B：[Checklist ZIP](packages/checklist/submission.zip)，SHA256 `f002c3c5cba1f629f2cce7608d2d72ac389af8a3ee03760257e1aff011844798`。
- C：[Prompt-only CURE ZIP](packages/cure_v01/submission.zip)，SHA256 `01e2a6271cab07356b7696cc21d82d9011ce88869a4a2bd4df68c62138a7634c`。

两ZIP均只有官方配置和Prompt四文件。Python状态/选择器、研究worker、机制修复脚本与日志不在提交包内。可提交机制目前是Prompt-only；确定性选择只在离线研究重放中执行。没有Gemma修复率、GPU实验或新增榜单分数。

## CPU复现

本机纯CPU：`python -m unittest cure.tests.test_state cure.tests.test_selector cure.tests.test_runtime cure.tests.test_mechanisms -v`。

完整官方Linux/API检查使用 [cpu-r03.ipynb](notebooks/cpu-r03.ipynb) 和 [对应metadata](notebooks/cpu-r03-metadata.json)。Notebook自带冻结源码，只需官方Wheelhouse的CPU运行环境，不下载模型权重、不启用GPU。换账号运行需修改metadata的kernel所属用户，保留官方数据挂载。重放应写新目录，不能覆盖已有证据。

当前执行门为 [cpu-r03/cpu_gate.json](results/cpu-r03/cpu_gate.json)。研究运行入口和spec字段见设计文档；此入口不启动模型服务。构建新CPU注册用 `python -m cure.build NEW_REVISION`；完整工作区会先验证原有私有证据，干净clone可直接重放已保存Notebook，不能伪称具有缺失的私有历史。

## 证据

[结果索引说明](results/README.md) 列出首轮失败、中间验证、最终门与原始档案。CPU门只放行后续预注册的小型机制实验；不支持宣称CURE优于Checklist。
