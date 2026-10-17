# CURE V0.1：可运行的研究原型与 Prompt-only 提交候选

研究执行器版本 `0.1.0`。起点 `972d1dd940db3910dd78685d6e37152e96ab514b`；开始时远程默认HEAD为 `0b0909df0177affa1eafe92bac679199235e4fd9`，远程 `feat/v0-coding-agent` 为972d1dd，未有CURE分支/实现。新分支 `feat/cure-v01` 从972d1dd创建。没有改写此前四份研究报告。

## 交付能力与边界

| 部分 | 已实现的能力 | 能否进入本次提交ZIP |
| --- | --- | --- |
| B：`candidates/checklist/` | 顺序契约检查清单 | 可编译的官方YAML/Prompt候选；31B、六工具、单Agent、无LoRA |
| C：`candidates/cure_v01/` | **Prompt-only CURE**：模型维护简短契约、更新证据、比较行动并输出解释 | 同上；状态维护、遵守策略与记录完整性取决于Gemma，CPU编译不证明其遵从 |
| `contract_state.py` / `action_selector.py` | 可执行的、确定性、可单测的研究状态与启发式选择器 | **未打包、未在官方Agent循环中强制执行** |
| `worker.py` / `runner.py` | 参数化研究执行器、上下文准入、持久化、被动契约观测 | 研究侧；**不修改官方评分Harness、不进入Agent ZIP** |
| `mechanisms.py` | 控制变量下真实CPU命令/测试与脚本策略重放 | 机制研究；不是Gemma修复实验、不是Kaggle成功率 |

官方配置可表达C的Prompt与合法生成参数，不能把本地Python选择器注册为评分系统的私有主循环。官方技能脚本机制不等于禁止所有辅助Python；本原型没有使用技能、额外工具或自定义回调进入提交包。即使以后让模型通过run_command调用一个策略脚本，模型是否调用和遵从仍是另一问题，不能称为评分环境中的确定性外部控制。

## 契约状态

`ContractState`包含 requirement、evidence、uncertainty、impact、verification_status、proposed_probe，另有 located/inspected/ready_to_edit/edited 标志。`ContractBook`最多六项契约，每项保留最近八条、每条最多400字符的证据摘要、原结果引用和SHA；历史原文在单独日志，状态不存完整文件。淘汰证据的数量显式记录。

证据区分 `observation`（实际工具返回字节）、`model_inference`（模型解释）、`unconfirmed_hypothesis`（未确认假设）。后两者不能降低不确定性、建立可编辑事实或标记验证通过。`passed`必须引用零退出验证结果；普通读取的exit0不是验证。**工具返回真实，不等于对其根因解释真实。** 语义标注由调用方负责，受控场景使用显式decoder，不冒充通用证据理解器。

更新遇到明确反证时增加contradiction_count、提升不确定性、清除inspected/ready_to_edit并重开验证。原requirement保留。公开候选由模型以类似含义维护文本状态；研究侧不把模型发出的JSON自动升级为观测事实。

## 主动行动选择

选择器在当前契约上生成locate/inspect/probe/edit/verify候选，并加上submit。资格门负责避免无定位直接编辑、无具体探针反复probe、修改后无验证。优先级是 `人工定义收益分 / 预计秒数`，结合impact和uncertainty；它是**排序规则，不是概率或经过学习的期望信息增益**。预计每行动一个抽象工具操作，实际时间/调用数另外记录。

| 条件 | 可观察决策 |
| --- | --- |
| 无定位证据 | locate |
| 定位已有但调用/接口未查明或被反证 | inspect |
| 已检查但关键行为未知且有具体探针 | probe |
| 证据支持具体修改 | edit |
| 已编辑、缺成功验证 | verify |
| 全部相关验证通过且有Patch，或预算进入收尾 | submit（可带未解决风险） |
| 剩余工具/时间不足 | 不执行额外工具；保留证据，不虚构Patch |

每次记录：状态快照、完整候选及资格/理由/成本、选中动作、实际工具结果引用/哈希、实际耗时/工具数，以及在**相同剩余预算**下“没有新观测”的下一步与更新后的下一步。单测进一步固定相同预算，证明反证能使edit变成inspect，而非只因时间变化。

已知弱点：收益/成本为人工初值；不确定性不校准；反复失败没有有效的备选修复生成器；低工具预算下预留规则可能过于保守。机制负例会保留，不为获得漂亮结果而事后改参数。

## B/C共同配置和包装

两个候选共用：`gemma-4-31b-it-qat-w4a16-ct`，六工具get_status/run_command/read_file/edit_file/write_file/submit_patch；temperature0.2、top_p0.95、top_k40、seed17、输出8192、thinking4096、include_thoughts=true；Agent300秒、60工具、单命令120秒。没有宣称这是最优预算。

`build.py`按四文件白名单产生确定性ZIP，根目录含agent.yaml；ZIP不含cure Python、控制器、测试、实验记录或参考答案。B/C共享安全边界段，变化在契约清单与主动决策段；名字/描述是标签差异。C的额外Prompt与可见JSON日志是实际开销，后续必须通过日志匹配消融区分。

所有ZIP与CPU注册版本禁止覆盖；相同字节允许复用，新内容必须用新身份。V0/V1/S0、r12、Pilot、正式配对01及原始证据保持冻结。新结果只放 `cure/results/` 与独立ignored下载目录。

## 独立研究执行器

读取 [NEXT_EXPERIMENTS.md](../NEXT_EXPERIMENTS.md) 后，从r12 worker派生新模块，继承其**未修改的**RequestGuard、DurableContext/Evaluator/SubprocessManager、Journal、supervisor、Windows Job与四态分类。`ResearchConfig`替代480秒与16384断言，编译后核对候选实际生成设置与注册值，出站参数漂移即拒绝。未封顶的摘要请求使用登记的输出上限；原Issue逐字保留，tokenizer计数失败不发送生成。

默认时间表：准备180 + Agent330（300原生+30宽限）+ 保存60 + verifier准备180 + apply60 + verify300 + persist60 + cleanup120 + safety60 = **1350秒外层**。五分钟Agent与五分钟Verifier互不挤占；按完整预算承认准备/清理成本。注册值可改变Agent时间/工具/输出/thinking，Phase2上限保留300秒。研究上下文上限32768、安全量1024，与r12一致；thinking不额外重复加到输出预留。

`ContractObserver`从原生ADK事件被动记录工具结果摘要与C的 `<cure>` 模型报告；去重非partial事件，不注册新工具，不把模型报告当真实验证，也不改变模型下一步。原始完整ADK事件、Agent边界Trace、提交Patch和Phase2证据继续由r12观察器保存。其自身开销只用于研究，不能把开发控制器的保护假称已包含在四文件提交ZIP中。

线上observer不会自动重建可信ContractState或替模型补写遗漏记录。当前只解析完整非thought文本part中的标记；跨part、缺失或格式损坏的声明存在观测缺口，原始事件仍保留。未来评测应报告记录覆盖率，并从两臂原生工具序列复核行动，不能把模型自报 `decision_changed` 当作已经证实的策略变化。

官方编译器→ADK→LiteLLM→mocked HTTP的CPU测试检查实际请求body：输出、thinking启停/预算、seed、工具结果一次JSON编码，以及include_thoughts对历史保留的影响。mock响应不经过vLLM，**不能证明vLLM执行thinking预算、tokenize模板或真实Gemma行动**。真实vLLM端行为是最小GPU门要验证的内容。

研究运行入口：`python -m cure.runner SPEC.json NEW_RUN_DIR --cpu-gate CPU_GATE.json`。spec需包含research_config、candidate_hashes、agent_dir、任务路径/ID/base/Issue哈希、snapshots/wheels/graphs/embeddings路径、model_alias/model_path/base_url。运行前必须有通过的、源哈希匹配的CPU gate；旧gate/缺失/源漂移拒绝，运行目录不复用。没有自动GPU启动或正式提交入口。

## 复现与验收

- `python -m unittest cure.tests.test_state cure.tests.test_selector cure.tests.test_runtime cure.tests.test_mechanisms -v`：本机纯CPU机制/参数单测，不需要官方Linux运行时。
- `python -m cure.mechanisms NEW_DIRECTORY`：12条真实CPU脚本重放；必须新目录。
- `python -m cure.build NEW_CPU_REVISION`：新CPU注册、分离的候选ZIP与Kaggle CPU Notebook；原始私有证据不进bundle。
- 官方Linux上 `python -m cure.cpu_validation REV OUTPUT`：运行现有38项官方/API与控制器测试、新测试、HTTP语义矩阵与机制场景，保存日志；跳过或失败不能放行。

实际执行结果和失败记录见 [MECHANISM_RESULTS.md](MECHANISM_RESULTS.md)。CPU机制测试只能支持“规则实现确能对证据/预算改变动作”；Prompt-only C是否产生同样行为以及是否提高修复率，须按 [ABLATION_PLAN.md](ABLATION_PLAN.md) 的小型GPU配对另验。

构建使用仓库内 `notebooks/install_official.py` 与CPU metadata模板，不再依赖旧ignored Notebook。现有完整工作区的build会先验证私有历史保留清单；干净clone没有这些原始私有文件时，不应伪称通过该保留检查，可直接使用随仓库提供的CPU Notebook重放公开代码/API门。安装使用官方挂载Wheelhouse；未来GPU运行仍须按实验协议固定Wheel字节与模型身份，CPU代码哈希门不是所有部署环境差异的自动证明。
