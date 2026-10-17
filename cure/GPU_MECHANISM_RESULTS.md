# CURE V0.1 首次真实GPU机制实验：首对门禁失败，按协议停止

2026-10-17，实验 `cure-gpu-mechanism-01`。**Checklist B完成真实Gemma修复与Phase 2；CURE C在ADK指令预处理时退出，没有发送首次模型请求。后续六次全部not_run。** 本轮没有可评估的完整机制配对，不能比较CURE与Checklist的修复能力，也不计算Kaggle Resolution Rate。S0的正式0.13分不属于本实验。

预注册于提交 `e345fe3`，GPU启动前已推送；[机器协议](gpu-study-01/protocol.json) SHA256为 `5a4c237f3ec7c5f7dd9927769b283831a024317192f47efe8bf9a5144c8bbbb5`。[执行说明](gpu-study-01/PROTOCOL.md) 固定了四个新场景、B/C交替顺序、预算及全局停止规则。GPU Notebook [smoke](https://www.kaggle.com/code/wudangdexiaodoashi/gemma4-cure-mechanism-01-smoke) 保存版本1的账号API状态为COMPLETE；**这不等于实验门通过**，实际 [batch_gate.json](gpu-study-01/results/smoke/batch_gate.json) 为false。

## 冻结与CPU预检

模型固定官方31B QAT版本 `/2`、4×L4；两个冻结ZIP没有改字节：B `f002c3c5cba1f629f2cce7608d2d72ac389af8a3ee03760257e1aff011844798`，C `01e2a6271cab07356b7696cc21d82d9011ce88869a4a2bd4df68c62138a7634c`。300秒Agent/60工具，输出8192、thinking4096、include_thoughts=true、seed17、temperature0.2/top_p0.95/top_k40，六原生工具、单Agent。上下文、阶段截止、Patch持久化与取消沿用原研究核心。没有LoRA、S0改动、正式提交或新榜单分数。

GPU前新增CPU预检中，原有63项再次通过。四个新场景的基线/参考检查及四份实际官方Phase 2验证通过；它们是脚本Phase1参考验证，**不是模型修复**。[CPU最终日志](gpu-study-01/results/cpu-r02/study.log) 共4项测试方法，包含四个Phase2子案例。首轮CPU失败与测试驱动修正也保留，见 [CPU说明](gpu-study-01/CPU_PREFLIGHT_NOTES.md)。没有修改任务、B/C Prompt或GPU运行核心来适配这些结果。

CPU门存在明确缺口：它覆盖了官方编译器→ADK请求对象→LiteLLM/HTTP参数，但未让**两个冻结候选分别通过完整Runner的instruction插值预处理**。因此编译通过没有发现下述C启动错误。这是本项目的门禁遗漏，不能据63/63声称C候选已能运行。

## 实际运行与成本

| 指标 | B Checklist | C CURE V0.1 |
| --- | --- | --- |
| 场景 | lumen_interface_01 | 同一场景、base、Issue和预算 |
| 规范化结果 | resolved | **unknown：无确认验证结论** |
| 官方原始resolved / test_exit_code | true / 0 | false / -1，原值保留，不能当确认失败 |
| HTTP实际LLM请求 / 官方LLM调用 | 14 / 14 | 0 / 0 |
| 原生工具调用（含submit） / 官方计费计数 | 13 / 12 | 0 / 0 |
| 实际服务器input / output / total tokens | 48,353 / 2,629 / 50,982 | 0 / 0 / 0，确认在生成前退出 |
| 官方total_tokens原值 | 0，占位，不能当真实消耗 | 0 |
| Agent计时 | 76.002秒 | 0.378秒，预处理退出，非推理速度 |
| 官方TaskResult计时 | 79.000秒 | 1.075秒 |
| 独立worker完整计时 | 92.197秒 | 14.532秒 |
| Patch | 978字节；新增入口、导出及repro.py | 0字节，没有修改 |
| 真正Phase2 | 新Verifier sandbox，2 passed，exit0，执行1.181秒 | 未运行 |
| 子进程树停止 / 沙盒清理 | true / true | true / true |

官方计数不计submit_patch，故B有13条工具调用事件、12个budget工具计数；两者都保留。不能拿C的零tokens/短时长解释成低成本或主动选择更高效，因为它完全未运行Gemma。无有效C执行，**C相对B的调查、时间与token增量不可估计**。

Notebook日志最后时间约1117.7秒，包含安装、模型全文件哈希、模型启动、基础设施probe和两次worker；不是两个Agent推理耗时之和。另有一条共同基础设施READY生成，实际24 input+95 output=119 tokens，单列于 [gpu_probe.json](gpu-study-01/results/smoke/gpu_probe.json)，未混入B/C任务指标。

数据见 [八槽位完整汇总](gpu-study-01/summary.json)、[B原始结果](gpu-study-01/results/smoke/runs/01-lumen_interface_01-checklist/official_result.json)、[C原始结果](gpu-study-01/results/smoke/runs/02-lumen_interface_01-cure_v01/official_result.json)。独立归因将C失败阶段标为 `agent_instruction_preprocess`；原r12归一化记录因末阶段为cleanup而写的failure_stage仍原样保留，不拿它解释根因。

## 真实请求与证据门

B的14条最终HTTP请求均路由至实际31B版本2路径，生成参数符合冻结值；每条/tokenize计数与对应vLLM响应prompt_tokens一致，最大输入5143。所有请求保留完整原Issue；工具结果JSON只编码一次；13条后续请求实际保留assistant reasoning_content历史，14份原始响应含reasoning。未出现length结束。该证据支持当前B路径的实际参数/历史处理，**不证明每次thinking恰好耗满4096**，也不能替未启动的C背书。

超界probe使用真正/tokenize并在生成前拒绝，见 [oversize_probe.json](gpu-study-01/results/smoke/oversize_probe.json)。逐请求原始参数/响应/usage见 [B HTTP记录](gpu-study-01/results/smoke/runs/01-lumen_interface_01-checklist/http_wire.jsonl)；[B门禁检查](gpu-study-01/results/smoke/runs/01-lumen_interface_01-checklist/mechanism_audit.json) 全通过。

模型在首次生成前对全部文件实测SHA，[模型manifest](gpu-study-01/results/smoke/model_identity.json) 摘要为 `53e2e2fbd72d65edf6af3477b6950c3b4d8e456865dcdbd65530e654469d22e2`，权重model.safetensors为 `1b9b1d622a93f02c0d33f98e502f233b5d707443af6ddc464ed0bf5498506c20`。挂载Wheelhouse逐文件匹配预注册SHA；未自动升级。

B工具命令只读取初始workspace、公开测试和自行生成的repro；未见向评估侧文件的读取。HTTP输入未包含隐藏test_patch，工具结果中也未见隐藏测试；独立测试只进入新的Verifier sandbox。GPU包排除了本轮参考修复/场景生成器；原生subprocess并不是恶意代码安全边界，这里是轨迹审计结论，不是绝对隔离证明。

## 逐事件机制判定

完整26条B call/response与C零事件见 [TOOL_TIMELINE.md](gpu-study-01/TOOL_TIMELINE.md)。按实际工具调用编号归纳：

| B工具号 | 原生行动及观察 | C对应情况 |
| --- | --- | --- |
| 1–2 | 列目录、读codec，定位旧入口 | 无事件 |
| 3 | 读client，看到getattr(codec,"render")和header="legacy" | 无事件 |
| 4–5 | 读迁移文档和导出；旧“无caller”文档被代码否定 | 无事件 |
| 6–7 | 写repro并运行，确认旧输出legacy:test | 无事件 |
| 8–9 | 保留render，新增encode_packet并导出 | 无事件 |
| 10–11 | 更新repro后重跑，确认大小写、新入口及旧输出 | 无事件 |
| 12 | 公开测试1 passed | 无事件 |
| 13 | submit_patch成功，978字节 | 无事件 |

1. **是否发现相同关键契约？** B发现新增入口、包导出、旧caller与大小写保持；C未得到模型请求，无法比较。
2. **反证后是否改向？** B在读真实caller后保持兼容，并否定迁移文档假设；未见它此前采纳“render未使用/可以删除”的错误计划。按预注册定义属于发现契约和规避错误，**不是已证明的假设反转**。C无机会，机制不可评估。
3. **有实际工具证据吗？** B第3–7次调查/复现、第8–11次兼容实现/复核是原生证据；C没有，不能用自报decision_changed补足。
4. **无效读取/重复测试？** B无相同文件的重复读取；同名repro前后运行发生在编辑前后，属于有效回归。C额外开销未知。B没有调用get_status或显式git diff，还把scratch repro.py留进Patch，未完全遵循Prompt的工作区/复核要求；Phase2通过不等于行为规程全遵守。
5. **Patch有效吗？** B通过实际应用与隐藏测试；C空Patch。
6. **真正Phase2？** 仅B完成，两项隐藏测试通过；C没有，不能写成验证失败。
7. **成本？** 见上表；没有完整有效配对，不报告成本优势。

## C失败归因与停止

[C错误日志](gpu-study-01/results/smoke/runs/02-lumen_interface_01-cure_v01/worker.stderr.log) 的真实堆栈为 `Runner → _process_agent_instruction → inject_session_state → KeyError: Context variable not found: JSON`。冻结Prompt中的说明 `<cure>{JSON}</cure>` 触发ADK的会话变量插值；会话没有JSON变量。错误发生在模型调用之前，因此没有HTTP请求、模型/工具事件、有效Patch或Phase2。它是**候选与ADK模板的兼容性错误**，不是Gemma解题失败、GPU显存不足、上下文越界或调查耗尽时间。

官方result虽然含resolved=false与status=SUCCESS，但test_exit_code=-1、test_output空，审计保持unknown。C有错误边界/原生Trace壳及空Patch检查点，不能描述为完整模型Trace。两次worker均确认进程树退出及sandbox清理；官方server.stop返回，记录保留。未另做模型服务所有GPU子进程的独立退出快照，不扩大清理证据的含义。

首对整体证据门为false。按原协议，harbor、cedar、orion各B/C共六次全部 **not_run**；未创建它们的GPU执行Notebook、未挑结果补跑、未替换当前C Prompt。Notebook状态COMPLETE只说明外层程序归档结束，不能改变停止结论。

## 决策与最小下一步

**目前不进入真实公开任务配对。** 这轮没有证实或证伪Gemma中的CURE主动改向能力，只证明当前冻结C候选不能通过完整ADK启动路径。先解决兼容性比新增训练或决策策略更优先。

最小修正建议（**未实施、未GPU验证**）：从当前C派生独立新候选，仅将说明行中会被插值的字面 `{JSON}` 换为不构成ADK变量的描述，例如 `<cure>JSON object</cure>`，保留真正JSON示例和算法要求。不要假设双花括号可以转义：当前ADK正则会剥掉连续花括号。旧C及其ZIP/SHA保持冻结。

新增门禁应让B和新C分别通过真实ADK Runner首步、空session state、mock HTTP捕获，验证发出了第一次请求且完整Prompt/JSON示例未被插值损坏；继续保留已有63项及预算/持久化检查。随后另行注册新的GPU首对，从B/C各一次重新开始，**不能复用本轮B去拼接一个修正后的C**。仅启动兼容修正，不因本场景结果改变算法Prompt；通过后才再讨论真实公开任务。

## 完整性与原始档案

- [GPU原始包](gpu-study-01/results/smoke/evidence.zip)：`37c81c3cc89ddca69f8858f28015522f2f48af6e1781e1d44689885619c70639`。
- [CPU首轮失败包](gpu-study-01/results/cpu/evidence.zip)：`bfbf2628a8a6d361390472312f495d08e42af8bbb7e841435a121d610bdc7837`。
- [CPU通过包](gpu-study-01/results/cpu-r02/evidence.zip)：`7f120cf9caecf9b97bf29be7cd2044522fe225b3a026f15460e2c17e50f30f51`。
- [B原生Trace](gpu-study-01/results/smoke/runs/01-lumen_interface_01-checklist/official_trace.json)、[B Patch](gpu-study-01/results/smoke/runs/01-lumen_interface_01-checklist/latest.patch)、[B Phase2](gpu-study-01/results/smoke/runs/01-lumen_interface_01-checklist/phase2_execution.json)。
- [C原生错误Trace](gpu-study-01/results/smoke/runs/02-lumen_interface_01-cure_v01/harness/traces/trace_lumen_interface_01.json)、[C空Patch](gpu-study-01/results/smoke/runs/02-lumen_interface_01-cure_v01/latest.patch)、[C错误边界](gpu-study-01/results/smoke/runs/02-lumen_interface_01-cure_v01/agent_boundary.json)。

三份原始ZIP、逐成员SHA、outer及nested evidence_manifest和CRC均独立复核；展示的日志/Trace/Patch逐字节等于档案成员。76项旧冻结文件、CURE原交付73项和原CPU门59项源码均保持不变。结果汇总保留官方原值，另加规范化归因。完整交付文件哈希见 [delivery-manifest.json](gpu-study-01/delivery-manifest.json)。
