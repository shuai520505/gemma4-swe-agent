# C1真实GPU首对：兼容修复通过，主动改向与成功率收益尚未证实

2026-10-17，独立实验 `cure-gpu-mechanism-02-c1`。新的B/C1首对均完成真实Gemma推理、有效Patch、官方Phase2和任务进程清理；没有复用上次B的轨迹。原实验01保持停止，所有原始记录不变。

| 必须独立判断的事项 | 实际结论 |
| --- | --- |
| **A：ADK兼容是否修复** | **是，已测路径通过**。完整Runner CPU门通过，真实C1模型/工具请求及Phase2通过，无JSON变量错误。 |
| **B：CURE决策机制是否出现** | **只观察到部分状态表达与契约验证**。开始/提交前各一份JSON，未持续逐工具更新；未确认错误假设被反证后发生行动改向，未证明状态/成本比较驱动选择。 |
| **C：是否提高修复成功率** | **没有支持证据**。一个已暴露合成配对，两臂都成功且最终Patch完全相同，不能推导Kaggle Resolution Rate或泛化增益。 |

## 候选、CPU门与预注册

C1只将说明标记 `<cure>{JSON}</cure>` 改为 `<cure>JSON object</cure>`，其余Prompt、JSON示例、三个YAML、模型/工具/预算/采样均逐字节保持。新C1 ZIP SHA256：`c1001800838f1465c1a6414685db239fb03f9a69b45bba6ff34c6232a6f2e612`，旧C ZIP仍为 `01e2a6271cab07356b7696cc21d82d9011ce88869a4a2bd4df68c62138a7634c`。[精确Diff与新旧SHA](gpu-study-02-c1/candidate-derivation.json)、[Diff文件](gpu-study-02-c1/candidate-exact.diff)、[C1提交包](packages/cure_v01_c1/submission.zip)。没有将私有控制器、测试或参考修复加入提交包。

官方CPU上原有63项及新增5项全部通过，无跳过：真实Runner+空Session State+模拟HTTP中，B/C1各发出1次请求，完整Prompt和真正JSON示例保持不变；旧C和双花括号负例均在HTTP前因JSON状态变量报错。全量花括号扫描只发现旧C的 `{JSON}` 会被当变量。详情见 [CPU兼容报告](gpu-study-02-c1/C1_COMPATIBILITY.md) 和 [完整Runner门](gpu-study-02-c1/results/cpu/full_runner_cpu_gate.json)。**模拟HTTP不是Gemma推理。**

新协议于提交 `2823045` 推送，GPU启动前CPU证据于 `ebc28ec` 推送。[协议](gpu-study-02-c1/protocol.json) SHA256为 `c47ef237d0b95089ee117cee75c8b0c836270bcb93d350fc2c34bdb32a28864c`，固定B→C1顺序、同一初始tgz/base/Issue、全部模型文件及Wheelhouse SHA、全局停止规则。模型官方31B QAT版本2、4×L4、六工具、单Agent；300秒/60工具、8192输出/4096 thinking、include_thoughts=true、seed17、temperature0.2/top_p0.95/top_k40，沿用原上下文/超时/Patch/清理保护。

实际 [GPU Notebook](https://www.kaggle.com/code/wudangdexiaodoashi/gemma4-cure-mechanism-02-c1-smoke) 保存版本1为COMPLETE，且 [batch_gate](gpu-study-02-c1/results/smoke/batch_gate.json) 为true。B与C1从相同干净快照分别建立全新Agent/Verifier sandbox。**lumen场景和前一次B行为已经被研究者观察，故本轮是探索性验证，不是独立泛化实验。**

## 真实结果与额外成本

| 指标 | 本轮新B | 本轮C1 | C1−B |
| --- | ---: | ---: | ---: |
| 官方resolved / test_exit_code | true / 0 | true / 0 | 结果相同 |
| 独立Phase2 | 2 passed | 2 passed | 均完成 |
| HTTP请求 / 官方LLM调用 | 16 / 16 | 15 / 15 | −1 |
| 官方工具计数 | 13 | 13 | 0 |
| 原生工具事件（含提交） | 15 | 14 | −1 |
| input tokens | 58,616 | 62,838 | +4,222 |
| output tokens | 2,747 | 3,147 | +400 |
| total tokens | 61,363 | 65,985 | **+4,622（约7.5%）** |
| Agent计时 | 79.564秒 | 90.874秒 | **+11.311秒（约14.2%）** |
| 官方TaskResult计时 | 82.450秒 | 93.500秒 | +11.050秒 |
| 完整worker计时 | 95.176秒 | 106.694秒 | +11.518秒 |
| 最终Patch | 497字节、2文件 | 497字节、2文件 | 逐字节相同 |
| 进程树停止 / sandbox清理 | true / true | true / true | 均确认 |

Token来自实际vLLM HTTP usage；两份官方TaskResult的total_tokens仍为0占位，未当真实消耗。input是各次请求报告的累计输入量，不能当作单次上下文长度。官方工具计数不计submit_patch；B提交两次、C1一次，所以同时保留原生事件口径。完整数据见 [summary.json](gpu-study-02-c1/summary.json)。

C1在300秒Agent预算中使用约90.87秒、13/60个计费工具，**没有观察到契约记录挤占编辑或提交预算**。但它仍多耗时/Token。不同Prompt长度、两份JSON、探测拆分和B的额外scratch清理/重提交流程同时变化，不能把全部增量因果归于“日志开销”，单次运行也不能估计普遍成本。没有输出length截断。

两臂均只读相关文件一次。C1比B多读一次公开测试，属于相关调查；C1将旧行为、新入口、包导出拆成三个检查，B用一个verify.py合并。基线/编辑后重跑验证的是不同工作树，不当作无效重复。B先提交了含scratch的1154字节Patch，随后清理两份脚本并重提交为497字节；历史检查点全部保留，未只保留较好结果。B因此未完全遵守候选“只提交一次”的要求；C1一次提交且未遗留scratch。这些是本次行为观察，不是策略优势估计。

Notebook日志最后时间约1253.06秒，包含安装、模型全文件SHA、启动和两次任务。另有共同基础设施READY probe消耗24 input+95 output=119 tokens，未混入任一臂。没有LoRA、S0改动、正式榜单提交或新分数。

## 契约状态是否真正迁移

C1首次真实请求的system包含完整候选Prompt。原始HTTP与ADK事件都确认出现两份有效可见JSON：第1次模型请求附在首次工具调用前，第14次附在submit_patch前。两份均保留四项契约：新入口、包导出、旧caller行为、确认render调用方。末份将验证状态从unverified改为verified，caller不确定性由medium变low；后者有实际caller读取/行为探测支持。这里的verified是Agent自报的自检状态，**不是它预先获知隐藏Phase2**。

但完整14次工具调用只有2次伴随状态记录（2/14），中间12次没有可见的逐结果更新；不是观察器漏解析，因为原始HTTP可见content也只有这两份。两份alternatives均为空，提交前previous_result仍为none；无法从记录重建中途的成本/不确定性比较。初始/末尾JSON分别1195/1119字符，没有将它们的字符数冒充准确Token开销。**状态格式部分遵从已观察；持续主动选择未证实。**

### 原生行动对照

完整call/response见 [TOOL_TIMELINE.md](gpu-study-02-c1/TOOL_TIMELINE.md)，下表的编号按每臂工具调用计数：

| 阶段 | B | C1 | 可支持的观察 |
| --- | --- | --- | --- |
| 定位/调查 | #1目录；#2迁移文档、#3 codec、#4 caller | #1目录；#2 codec、#3迁移文档、#4 caller | 都查了真实调用方，没有依赖文档假设直接删除render |
| 旧行为复现 | #5写repro、#6运行；#7读导出 | #5内联复现；#6读导出、#7读公开测试 | 都确认legacy:test和caller契约 |
| 修改 | #8/#9新增函数和导出，保留render | #8/#9相同修改 | 最终两文件diff相同 |
| 回归 | #10写verify、#11运行、#12公开测试 | #10旧行为、#11新入口、#12导出、#13公开测试 | 都有实际行为/测试证据 |
| 收尾 | #13提交、#14清理scratch、#15重提交 | #14提交，附第二份契约JSON | Checklist也会根据收尾反馈修正操作，不能当作绝不会反思的弱基线 |

### 反证与改向判定

实际caller代码否定了迁移文档“render未使用”的假设；这是可确认的**仓库证据冲突**。然而两臂起初都将该假设当作待验证，没有可定位的先前声明/已选编辑计划表明模型相信“可以删除render”。随后它们调查、保留旧入口并验证，属于发现契约并规避错误。

因此，本轮没有形成预注册要求的“模型先采纳错误假设→工具反证→下一行动改向”机会，**不能计反证改向成功，也不能据此判定C1不会改向**。C1两份decision_changed均为false，但结论来自实际序列和此前主张审计，而非信任该字段。即使C1状态表达更显式，B也采取了相近调查/验证动作；不能证明这些状态因果驱动了选择。

独立于自报的结构化判断见 [mechanism-assessment.json](gpu-study-02-c1/mechanism-assessment.json)。同一实施者能看到臂标签与结果，没有第二位盲审；结果属于机制探索。

## 基础设施、完整性与决策

31条真实请求的模型路由、8192/4096/seed17及采样参数符合协议；每次/tokenize计数与服务器prompt_tokens一致。最大输入B为5453、C1为6338，保留完整Issue，工具结果单次JSON编码；16/15条响应含reasoning，15/14条后续请求保留reasoning历史。真实超界probe在生成前拒绝。两臂原生Trace、边界Trace、Patch、官方Phase2与worker清理证据齐全，严格门通过。模型/wheel字节与预注册清单一致。

原生工具路径只涉及workspace初始代码/公开测试/自建scratch；未见读取评估侧材料，HTTP输入没有隐藏测试。subprocess不是恶意代码安全边界，结论限于本次轨迹审计。server.stop返回；未增加模型服务所有GPU子进程的独立退出快照，不扩大该证据的含义。

建议保持B/C1冻结，**不基于本轮扩大为修复率或榜单提升宣称**。下一步若继续，应另行预注册新的、未观察场景，在自然运行中具有可确认的反证机会，审计记录覆盖与真正行动改向；必要时单独比较等长日志的Checklist，区分记录与决策的影响。本轮不自动开展这些实验，不训练或提交榜单。

原始交付：

- [完整GPU档案](gpu-study-02-c1/results/smoke/evidence.zip)，SHA256 `4108828cc749f81bb631bbfa2eab42138f794112e7def39daaff435300fe6e09`。
- [完整CPU档案](gpu-study-02-c1/results/cpu/evidence.zip)，SHA256 `f8079beec2e47f51ee36f3444899da2b84dcbf2c40d80d4ea34b5ce67ed455c3`。
- B：[Trace](gpu-study-02-c1/results/smoke/runs/01-lumen_interface_01-checklist/official_trace.json)、[Patch](gpu-study-02-c1/results/smoke/runs/01-lumen_interface_01-checklist/latest.patch)、[Phase2](gpu-study-02-c1/results/smoke/runs/01-lumen_interface_01-checklist/phase2_execution.json)。
- C1：[Trace](gpu-study-02-c1/results/smoke/runs/02-lumen_interface_01-cure_v01_c1/official_trace.json)、[Patch](gpu-study-02-c1/results/smoke/runs/02-lumen_interface_01-cure_v01_c1/latest.patch)、[Phase2](gpu-study-02-c1/results/smoke/runs/02-lumen_interface_01-cure_v01_c1/phase2_execution.json)。
- [SHA/CRC审计](gpu-study-02-c1/integrity-audit.json)：原实验01的135项、原CURE交付73项、旧基线76项及原CPU源码59项不变；本轮70项登记源码匹配。outer/nested ZIP原生manifest、成员哈希和展示副本均复核。两臂最终Patch相同，SHA256为 `443e3a03e6692bbe3de3465e79fdb24af240159ebae486ac892209b343866a6d`。
- [全部交付SHA](gpu-study-02-c1/delivery-manifest.json)。
