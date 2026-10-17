# CURE V0.1 CPU机制结果

这些结果来自**真实CPU命令、真实测试和脚本化修复动作**，没有Gemma生成，没有Kaggle正式题修复率。比较对象是Python固定顺序策略B与Python启发式选择器C；YAML候选B/C的Gemma行为尚待GPU检验。

## 本机受控重放

每臂使用同一fixture、同一probes/verify与同一个预设编辑器；C没有额外修复答案。四个正常场景各一次，另有预算不足和错误编辑两组负例，共12条重放。时间是实际子进程耗时之和，不含setup、Python决策/日志与冷启动；不能当作端到端GPU成本。工具数是fixture抽象操作数，不是官方LLM工具调用计费。

| 场景 | B实际操作 | C实际操作 | B/C秒数 | 结果 |
| --- | --- | --- | --- | --- |
| 接口命名与调用方兼容 | locate→inspect→probe→edit→verify→submit（6） | locate→inspect→probe→**inspect**→edit→verify→submit（7） | 2.327 / 2.922 | 两者预设修复均通过；C多一次调用方调查 |
| 依赖注入 | 同B顺序（6） | probe后重查caller（7） | 2.875 / 3.248 | 两者通过；C因反证重开调查 |
| 零值边界 | 标准顺序（6） | 标准顺序（6） | 3.015 / 3.018 | 两者通过；相同动作不意味着算法无状态 |
| 旧行为保持 | 标准顺序（6） | 标准顺序（6） | 2.638 / 2.469 | 两者通过；时间差为单次调度噪声，非速度提升证据 |
| 接口题仅6工具 | 完成修复和验证（6） | 多调查后提前submit，无Patch（5） | 3.468 / 2.671 | **C失败**：预留规则过于保守，额外调查有机会成本 |
| 错误编辑破坏旧行为 | verify发现失败后submit（6） | 再inspect/edit/verify，仍失败，最后带未验证修改submit（11） | 3.094 / 4.811 | **两者失败**；C额外5操作未救回，当前无有效备选修复器 |

原始结果、所有决策、工具输出、Patch和逐文件manifest见 [local-mechanisms-r01.zip](results/local-mechanisms-r01.zip)；[可读汇总](results/local-mechanisms-summary.json)。正常场景8次均通过只是预设修复与测试的自洽性，**不能宣称100% Agent修复率**。

## 是否真的因反证改变决策

`test_observation_changes_edit_to_inspect_at_same_budget`固定相同100秒/10工具：有定位/检查证据且ready_to_edit时选择edit；加入有引用/哈希的反证后，inspected/ready_to_edit清除，不确定性升高，选择inspect。控制了预算变化。其余优先级测试验证impact变化、具体probe、无预算不调用工具和收尾条件。

真实fixture中interface与dependency_injection的失败probe后，C重查caller，B按顺序继续edit。fixture decoder显式知道如何解释该受控工具结果；这证明**状态更新与规则分支可运行**，不是证明模型能自动理解任意反证。两臂使用相同脚本修复，故没有刻意制造B无法修题的弱基线。

每次选择记录了当时状态/证据、所有行动候选、理由、预计时间/工具、实际结果和同预算下一步对照。证据摘要有限，完整工具结果单独落盘；日志本身有额外CPU/磁盘成本，本轮未将其误算为模型token开销。未来GPU测试必须记录C的额外Prompt/可见JSON tokens。

## 官方CPU/API门

第一轮 `cpu-r01`：原有官方Linux/API与控制器 **38/38通过**；新增测试失败。根因是将submission.zip放入候选源码目录，官方validate_directory禁止该扩展名；18组语义子测试及后续编译因此未执行到请求阶段。原始失败包/日志保留，未当作模型或修复失败。

修正方式：ZIP移动到独立 `cure/packages/<arm>/submission.zip`，四文件源码目录保持纯净；ZIP字节/SHA不变。新增实际worker参数/异常落盘回归，随后使用新的CPU注册版本重跑。`cpu-r02` 的38项原有测试及23项新增测试通过；增加可移植构建模板和包装边界检查后，以新的 `cpu-r03` 再验证当前源码。

最终 **cpu-r03：38项原有测试 + 25项新增测试 = 63/63通过，0跳过**。Kaggle私有CPU Notebook `wudangdexiaodoashi/gemma4-cure-v01-cpu-r03` 保存版本1状态为COMPLETE。当前59个登记源码文件与实际CPU门哈希逐一一致。见 [最终gate](results/cpu-r03/cpu_gate.json)、[新增测试日志](results/cpu-r03/cure-tests.log)、[原有测试日志](results/cpu-r03/cpu_tests.log) 和 [完整原始包](results/cpu-r03/evidence.zip)。最终原始包SHA256为 `d5d3cba9a8ba28f7d43bd18f2b9190a7b14b41e7a2ede9acd5ae1e641be31b3b`；失败首轮和中间通过轮也完整保留，未覆盖或删除。

18组真实官方编译器→ADK→LiteLLM→**模拟HTTP响应**的检查通过：thinking 0/512/4096、include_thoughts 未指定/true/false、seed 未指定/17；确认出站8192输出上限、thinking参数、历史reasoning保留和工具结果单次JSON编码。请求body见 [HTTP证据](results/cpu-r03/http-request-cases.json)。这不是18次真实模型推理，未访问vLLM/Gemma。

独立worker回归使用47秒Agent、7工具、2048输出和thinking=0，实际检查编译/评估对象收到注册参数；模拟Verifier异常后Patch仍落盘、清理完成、缺少官方最终结果保持unknown。上下文临界值/超过1 token、参数漂移拒绝、取消/外层截止/清理延迟等由新增及原有38项回归覆盖。它们证明CPU路径和注入故障处理，不证明真实GPU任务一定无超时。原有76项冻结文件、r12的28项源码及历史ZIP哈希检查记录见 [保留检查](results/preservation-final.json)。

## 可提交能力与下一步

当前候选是 **Prompt-only CURE**；Python主动选择器在研究重放中确定执行，在官方Agent中不确定执行。被动observer记录真实ADK结果与模型自报，明确标注后者未验证，不增加工具或暗中给C帮助。提交包不含研究控制器。

本轮支持的结论：能根据新证据和预算改变动作的最小算法原型已实现，且可审计；已暴露低预算退化和重复无效修订两类失败。**没有支持“CURE提高Gemma比赛修复率”的证据。** 下一步最小GPU机制对照及证伪条件见 [ABLATION_PLAN.md](ABLATION_PLAN.md)。
