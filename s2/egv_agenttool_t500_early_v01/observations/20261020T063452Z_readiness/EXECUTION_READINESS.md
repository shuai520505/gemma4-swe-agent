# 两任务四运行：资源与待授权构建清单

当前：CPU Go；Quota Go；完整GPU Resource No-Go（机器/窗口/并发准入仍有UNKNOWN）；Execution Not Authorized；Algorithm Evidence 未取得。
这里的资源No-Go并非余额不足。没有新GPU、模型服务、正式提交或候选改动。

## 已核验的冻结内容

- 原A ZIP：13968b67844d1041bfb79b9f11fc21ae66fb36aee5b00d3b91c526d5d35da329。
- Early B ZIP：d1e815e770abbcc448325ad2a3c8785c62f6d3c63bc7f95700850748c048a487。
- 仅Main Prompt不同；agent/eval/child配置及child Prompt相同。相同31BQATv2、500秒共享、60计费工具、120秒命令、输出16384、thinking4096、seed17。
- rich_3676：A→B；fastapi_14492：B→A。完整4运行；旧八题独占集合不变；任务Issue/base/snapshot等绑定复核通过。
- 原官方Linux CPU02单次135/135的原始ZIP CRC/manifest通过，实际500.100秒边界、60次计费工具、空State Runner、修复前后委派/反证/修订/复验/显式提交证据仍匹配源码。
  本轮只重放证据和静态检查，没有重新声称执行135个官方Linux测试，更没有真实Gemma推理。
- 新增本地3项Duration回归、已有3项授权/窗口保护回归通过。
- 2281项Early冻结文件、基线11229项Git文件及64个ZIP的字节审计通过。
  92项已存在CRLF保留其旧raw SHA并核对规范化Git blob，没有重写历史。
- Notebook/payload/protocol/metadata SHA匹配GPU_DRAFT_FREEZE，载荷CRC、228项源码绑定、CPU验收、模型/任务wheel身份匹配。
  模型8个文件的冻结摘要与旧证据一致；未重新挂载远程实际模型/wheel字节，未来运行时仍须全量拒绝漂移。
- Notebook第一条AST为无条件raise；本轮只执行该单条raise验证拒绝，未执行整个cell。
  metadata仍enable_gpu=true，所以**即使有raise也不要上传试跑**：平台可能先分配资源。
- 保存Notebook列表无草案slug。源代码仍使用授权身份+4run配额标志检查；未经新授权不构建可执行版本。
- 每臂使用独立进程、会话、run目录、工作区、Verifier。输出目录含index/task/arm；不会把前臂Patch/Trace当作后臂输入。
  同一模型服务仅承接分离的请求；后端idle、HTTP生命周期、null/partial usage、worker/sandbox清理、JUnit分类、子Agent写入审计源码均在冻结绑定中。
  这些是源码/既有CPU证据准备，完整四运行协调器尚未经过真实GPU验收。

## 资源计算

| 规划项 | 秒 |
|---|---:|
| 4个Agent上限合计（已包含在Worker中，不重复相加） | 2000 |
| 4×(Worker1550+服务idle60) | 6440 |
| 模型启动 | 1200 |
| 安装 | 300 |
| 两个干净baseline各最多300 | 600 |
| 最后证据落盘/清理预留 | 900 |
| 总规划 | 9440 |
| 距10000窗口余量 | 560 |

开始模型启动时，全四运行+启动+落盘必须尚有8540秒，setup已耗时最多1460秒。
560秒仅为规划余量，额外哈希/I/O/平台抖动可能使门禁拒绝；不能保证全部完成。
Worker1550已涵盖Agent、Patch、原生Phase2、进程清理与证据保存；不改官方测试。
10000秒约2小时46分40秒，一般文档12小时窗口足以容纳，但账户/机器实际批准窗口尚未实测。
按旧单次4L4经验约2×wall计账并加600预留，冻结要求20600报告配额秒。
新余额87194.356，缺口0、余量66594.356；经验倍数不是通用平台计费保证。
即便取4×10000+600的敏感性情景40600，数字仍低于余额；这不是实测收费率。

## 后续授权后的准确步骤（本轮没有执行）

1. 保存一次新的raw HTTP配额及完整机器/会话只读准入；确认4×L4 eligibility、无冲突运行/保留、保存/启动限制与批准窗口至少10000秒。
   若无法确认，保持No-Go；不靠启动一个单臂实验来探测。
2. 获得明确的本实验4次GPU执行授权。仍不涉及正式榜单提交。
3. 在独立execution build目录创建授权记录和新Notebook/载荷manifest；绑定冻结A/B、两任务ABBA、CPU验收SHA、模型/wheel/task/source身份及预算。
   保留原DRAFT Notebook/协议/哈希不动；新的授权状态与Notebook SHA必须在首次推理前归档。
4. 使用官方CLI明确请求NvidiaL4及timeout10000，保存版本。此步会启动资源，当前禁止执行。
   账户审批/平台限制不合格即STOP，不自动换机器或缩减样本。
5. 先重验实际挂载模型/wheel/task字节，干净baseline及Compiler/真实请求语义、4×L4 TP4、启动生成/usage/context/idle门。
6. 严格rich_3676 A→B、fastapi_14492 B→A；每臂独立目录；无输出泄漏。每次开工前为所有剩余完整slots保留预算。
7. 普通可归因算法失败保留resolved=false并继续配对；环境/证据/泄漏/子Agent生产写入/未知HTTP/服务不空闲/清理/全局资源失败则按冻结STOP保留unknown及not_run。
8. 归档原生TaskResult/Phase2/JUnit/Trace/Patch/请求生命周期/服务器idle/清理与SHA；不补跑拼接、不用旧rich_3471替代。

现有身份、样本和Prompt不需要因配额解释修正而重新选题。
但必须增加独立的授权执行构建；如预算、样本、顺序、生成条件或停止规则实质变化，应在推理前另外预注册，不能修改旧冻结文件。

## 下次实验究竟要回答什么

主终点为每题官方完整resolved，unknown/not_run单列；两题不能证明总体修复率优越。
逐事件审核首次读到正确源码、有效生产编辑、首次EGV及Patch前后关系、真实断言/源码来源、可操作反证/交付、Main实际修订、针对性复验、旧行为、显式提交、诊断残留、截止、主子Token（缺失null/partial）、计费工具和worker/平台成本。
有效协作必须是“实际反证→真实交付→Main源码修正→区分性复验→原反证消除”。
模型自述、EGV调用次数或PASS报告不能替代工具证据；B更早调用但resolved下降不能判为更优。
0个反证的闭环率分母为0，记null；无效委派与重复检查照计成本。
