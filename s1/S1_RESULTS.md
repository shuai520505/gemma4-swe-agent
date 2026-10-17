# S1 研究结果：实现与受控执行，E1在任务前停止

**本轮没有得到任何完整Gemma修复配对，没有证据支持S1提分。** S0正式submission **57261002 / COMPLETE / Public Score 0.13** 保持不变，没有新榜单提交。已实现独立候选、参数化研究执行器、官方CPU/API/完整Runner门和受控GPU实验；GPU在启动探针因本项目API调用错误停止，修正后只运行CPU，不重启GPU拼接结果。

## 实际执行

| 阶段 | 真实输出 | 结论 |
| --- | --- | --- |
| CPU r01 | 61项，51通过/10失败 | 工具消息content:null在HTTP被省略；精确比较测试需处理这一个已知差异，GPU未启动 |
| CPU r02 | **63/63通过** | 五候选完整Compiler→空State ADK Runner→模拟HTTP；实际worker配置、预算/持久化/清理门通过 |
| GPU E1 smoke v1 | **ERROR**，任务前TypeError | 31B模型服务加载/路由、一次tokenize成功；首个生成请求未发出，A/B均not_run |
| CPU r03 | **66/66通过** | 复现旧缺参问题；修正后的同一启动探针函数通过真实官方客户端→模拟HTTP；禁止继续已停止GPU协议 |
| CPU r04 | **71/71通过** | 全局准入包含安装/模型哈希/启动，新增五个时钟边界测试；没有新GPU |
| E1四题筛选 | 八个槽位全not_run | 按全局止损未启动，不能计算修复率或赢家 |
| E2/E3/E4 | 独立候选与完整Runner CPU通过 | 未登记/执行GPU，无效果证据；无组合候选 |

原始输出分别在results/cpu-r01、cpu-r02、smoke、cpu-r03、cpu-r04。没有复用Pilot、formal-paired-01或CURE的模型轨迹/任务结果。原冻结S0、V0/V1、CURE、r12和历史ZIP未修改。

## GPU失败的直接原因与证据

实验ID `s1-e1-public-01`，预注册提交 `30cd362b04fadb9e3b1540693a842374121944e8`，协议SHA `37744d52e1980964028fca55719cbd68f9a46ad989b71c2fc7b93eccc93bf9e8`。

[实际Notebook](https://www.kaggle.com/code/wudangdexiaodoashi/gemma4-s1-e1-01-r02-smoke) 保存版本1。原始ZIP253808字节，SHA `eacbd9082ce6588b8f300923a156eefac58bfa93a3e1b58a5c10fdd54860806c`；CRC及136项manifest核验通过。

`results/smoke/session_exception.json`：`TypeError: LiteLLMClient.acompletion() missing 1 required positional argument: 'tools'`，位于冻结r02 session.py:79经RequestGuard调直接客户端时。官方源码的签名是`acompletion(self, model, messages, tools, **kwargs)`。该接口即便不使用工具也需显式tools=None。

这不是Gemma修复失败、Prompt失败、上下文越界或GPU不足。新执行器的启动探针漏参，原完整ADK Runner路径会自动提供tools，因而旧门没有覆盖它。这是本轮实现的失误；不能将它归咎于官方API变化。r03将同一探针提取为preflight.check_model，新增直接API路径回归，精确diff在revisions/r03。五个候选ZIP及Prompt保持原SHA，不包含算法调参。

已获得的GPU证据：41个Wheel与8个模型文件SHA匹配；vLLM0.19.1、31B version2、TP4、32768配置，health/models/tokenize返回200。访问日志中实际chat/completions POST **0次**，tokenize POST **1次**。没有任何Agent任务开始，未产生任务Trace、Patch、Phase2或可归属的Token/工具计数；这些项记null，不伪造空Patch或官方失败。

精确的启动探针tokenize payload/count/admission在该异常前未持久化，是信息缺口；只有端点访问日志，不能声称计数已与生成usage匹配。没有真实Gemma文本生成，因此仅模型加载部分成立，完整GPU基础设施门不通过。

finally保存vLLM原生日志并停止服务；server_cleanup.json核验7个已观测PID全部退出、无剩余、无强制kill。任务worker从未启动，因此没有任务sandbox或跨题并发。原协议STOP记录已保存，构建器和CPU测试均阻止继续生成该实验的GPU Notebook。本轮只执行这一个GPU保存版本。

## 配对与成本

计划smoke一题两臂、筛选四题八次，共10槽位，均not_run。Task confirmed failed=0、unknown=0，但**这不是0%或100%的成功率**：完整配对0，resolved差异和完整率估计均为null。逐槽位及四态汇总见results/e1-public-01-summary.json。主终点排除smoke。

GPU Notebook日志可观察跨度1162.571秒，约19.38分钟；以4张L4持续分配推算约1.29 GPU·小时。这是日志时长占用近似，不含排队/不可见平台阶段，也不是Kaggle扣费口径。没有Agent执行成本测量。未启动后续两批，避免再消耗其预留成本。

机器协议中的6.75节点小时/27 L4 GPU小时是三批启动/收尾与任务槽的**规划包络**，不能解释为平台计费保证。各任务外层1350秒独立于启动。失败的r02全局session时钟在session.run内开启，未含此前安装/模型哈希；r04已改为Notebook setup起点贯穿准入、保留完整槽及900秒收尾，并通过71项CPU门。该修正没有GPU复核，也不追改原协议。此次在任务前停止，没有测到完整批次的实际耗时。

## Q1：S0=0.13有哪些Trace支持的瓶颈

没有S0隐藏评分题逐题Trace，无法给0.13作全面失败归因。可以确认的是历史公开开发记录：

- Pilot01 Rich/V0有实际输入至少16385+输出16384>32768错误，38次读取/命令、无编辑/提交；支持上下文与探索风险，非当前S0隐藏题占比证明。
- 首次FastAPI V0首次写入270.240秒、5次完全相同读取；自拟入口与Phase2导入契约不符，且没有pytest/最终Diff命令。任务描述欠明确，不能声称换文件名必通过。
- Pilot Rich/V1实际98 passed/1 failed，遗漏实例环境注入路径；formal-paired-01六次非空Patch仍有行为断言失败，另有空Patch/Agent截止。支持E3/E4值得测试，不能证明Prompt必然有效。

来源为仓库原FAILURE_ANALYSIS.md、experiments/PILOT_01_AUDIT.md、experiments/formal-paired-01/REPORT.md及其原始证据。本轮不把它们拼入新实验。r12已经防止越界；“降低输出预留仍能提分”保持假设。

## Q2：优先投入哪个因素

下一次有限GPU首先完成**E1输出预算**单对兼容门：最干净、无需改Prompt，且有真实历史上下文冲突线索；这表示信息价值优先，不是预测8192最佳。若E1在完整开发对照没有修复收益，就不组合采用。策略因素优先E3有界定位，其后E4接口验证；E2关闭thinking可能损伤复杂推理，应在固定输出条件下独立测试，不混入E1。

## Q3/Q4：是否取得真实修复增益，是否可冻结S1探分

**均否。** 没有任何本轮完整任务配对或真实生成，连“只更快”都无法比较。E1结果未测定，不是被证明无效。当前不准入8192、thinking0、E3或E4为已证实提分因素，不生成组合S1，不准备带提分结论的正式榜单提交。

## Q5：下一项最低成本、高信息价值实验

r04 CPU已71/71通过；下一步须**新实验ID、重新预注册一个Requests重定向题A/B smoke**，同候选SHA/5分钟60工具/seed17、干净快照。此前没有Agent获得该题，未观察模型轨迹；可以解释为同题基础设施复核，仍不算独立泛化确认。CPU通过不替代真实probe、Token usage、Trace、Patch、Phase2、清理门。

单对Agent上限10分钟；按本次约19分钟启动，正常运行可先以约30–45分钟节点时规划，非保证。沿用完整阶段槽的保守预留为105分钟（2×22.5+45启动+15收尾），约7 L4 GPU小时规划量。只有新smoke完整通过才考虑新注册四题筛选；本轮没有启动该复核，没有正式提交授权流程。

尚未完成：真实E1配对及后续四题筛选；E2/E3/E4各自GPU消融；任何组合的独立确认；S1正式12小时预算与生产初始化开销验证；正式评分Notebook与榜分。5分钟/60工具仍是起点，不是最优配置。本研究subprocess与正式Docker初始化成本不能直接等同，因此没有生成S1正式提交就绪结论。
