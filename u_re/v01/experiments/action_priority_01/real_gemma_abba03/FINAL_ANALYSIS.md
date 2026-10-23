# GPU03_REAL_GEMMA_ABBA_COMPLETE

CPU端到端 Notebook140305458/v1 COMPLETE；唯一GPU03 Notebook140306593/v1 COMPLETE。原始GPU ZIP已按ID、owner/ref/slug、版本1、源码语义、载荷SHA及下载前后latest=1核验。四个独立真实Gemma Session按冻结ABBA顺序完成，原生resolved为false,true,true,true。没有正式Competition Submission。

|Run|Task|Candidate|Native resolved|Agent s|First production edit s|First local assertion support s|Charged tools|HTTP|Received tokens|Successful submits|Post-submit tools|
|---|---|---|---|---|---|---|---|---|---|---|---|
|1|fastapi_9425|A|false|264.284|NOT_OBSERVED|NOT_OBSERVED|26|26|179265|0|0|
|2|fastapi_9425|B|true|229.729|138.953|161.209|36|39|370159|1|0|
|3|fastapi_14786|B|true|79.085|30.341|32.911|15|17|124068|1|0|
|4|fastapi_14786|A|true|116.113|29.648|32.236|22|24|187475|2|4|

A=Frozen NoEGV；B=Frozen Action-First。计费工具调用不等于全部工具/模型请求。所有时间基于真实单调时钟事件，首次源码编辑是实际文件哈希变化的观测上界，初始快照解包不计为修复。首次局部支持来自模型自行编写、实际执行且与Issue一致的断言；它不等于整个任务修复。首次“可应用补丁”仅在可信原生Verifier应用最终补丁时被独立观察，分别270.125、235.422、84.864、121.891s；不冒充最早创建时刻或正确性证明。

## 成对结果与成本

- fastapi_9425：A未修改生产源码，留下3个诊断脚本；B在138.953s修改目标源码，最终Native通过。A的非空诊断Patch不算有效生产修复。
- fastapi_14786：两臂均通过，最终生产Patch SHA完全相同：b014f9881df30a205d9d5c6cab63e7de8c519805e96ea54fc4ded26eb9a9c509。A在29.648s编辑，B在30.341s编辑，B晚约0.693s。因此不支持“B在所有任务均更早首次编辑”。
- Both resolved1，A only0，B only1，Neither0，Unknown0。两题来自同一个仓库，不能推断总体SWE成功率或正式Public Score。
- A：1/2 resolved；Agent380.396s，Worker436.405s，48charged tools，50HTTP，prompt354907+completion11833=366740received tokens。
- B：2/2 resolved；Agent308.814s，Worker364.750s，51charged tools，56HTTP，prompt485356+completion8871=494227received tokens。
- B总Agent时长少18.82%，但charged tools多6.25%、HTTP多12%、received tokens多34.76%。不是全成本下降。按本次成功数摊分，A366740tokens/成功，B247113.5tokens/成功；这是包含失败任务成本的两题描述性比率，不是外推的经验成功成本。
- 显式成功提交比例A1/2，B2/2。A在14786重复成功提交一次，首次成功提交后又调用4个工具；B两次均没有提交后工具调用或重复提交。

## 失败、停止与回归边界

没有模型服务、隔离、Verifier或清理完整性STOP。全部106HTTP收到200响应且usage完整。没有300秒截止或60charged预算耗尽。

两个A运行触发了冻结的context reservation guard：max context32768，固定output reserve16384+safety1024，允许输入上限15360tokens。9425A实际输入15881，总reserved33289；14786A输入15431，总reserved32839。拒绝发生于下一次模型请求之前，属于固定上下文策略下的资源停止，不是vLLM服务崩溃。9425A停止时尚无生产修复，最终原生断言失败；14786A已有正确生产Patch，停止后仍由原生Verifier判定resolved=true。不能断言额外上下文必然能修好9425，也没有调整本轮的保留策略。

两臂在14786上运行较宽pytest集合时，实际遇到独立python-multipart缺失/collection问题；后续缩小范围的7项相关测试通过，可信原生9项测试也均通过。该环境限制属于Agent选择的宽测试命令，未阻断本轮原生评测；不能说整个FastAPI测试套件已通过。grep无匹配及合法反例断言失败不算无效操作。

A14786在公共工作区尝试增加2项正向回归断言，随后再次运行同一pytest命令，因此原始命令+生产哈希重复proxy=1，但测试输入已变化，保守的未变化断言测试重复计数为0。原生最终Patch排除了这些测试改动，原始评测覆盖物及输入身份未改变。未观察到弱化断言。A9425最终遗留repro.py/check_lenient.py/check_annotation.py；B两臂及A14786最终均只有生产文件变更。Native覆盖内未见新的旧行为回归；覆盖外风险仍未测量。

## CPU与GPU同载荷证明

共享生产ZIP SHA：ee6bf87f334c9b4ee67eb673fba32c92f6d43953b5ed308824d602521beb4470。CPU与GPU Notebook解包的生产文件逐项相同。CPU从生产Session入口连续进入：显式pins含CPU_GATE_PIN → 惰性导入fastapi_pilot_01 → 两道真实身份/基线 → GPU共用监督器启动独立Worker → 官方Compiler/ADK/六工具配置 → chroot源码修改/断言/207字节Patch → 显式提交 → 原生TaskResult/JUnit → HTTP事件 → 进程/沙箱/服务清理。CPU_MODEL=SCRIPTED_ONLY；6次CPU脚本化HTTP单独记账，GPU载荷内没有脚本化传输文件且GPU模式拒绝注入该传输。

GPU实际为4×NVIDIA L4，每张23659151360bytes，TP4；CUDA12.8，torch2.10.0+cu128，vLLM0.19.1。八个Gemma4 31B QAT v2模型/tokenizer/template文件SHA全部匹配，服务模型身份、后台日志及106个真实请求响应构成真实加载/推理证据。没有READY生成或额外SWE回合。

## 资源与原始证据

代码时钟1390.067s，其中Agent合计689.210s、非Agent代码700.857s。Worker总801.154s，Worker内非Agent111.944s，Worker外588.913s。初始化至共享入口97.393s，共享预检190.520s，从load_model到首个Worker prepare的上界297.899s（包括加载、健康/idle检查和子进程导入，不能叫纯权重加载耗时）。原生四次pytest执行合计约6.625s。显存容量已测，整个过程的峰值显存未独立采样，保持UNKNOWN。

实际GPU独立计费时长未知。账号报告配额从82016.632减至79195.524，差2821.108报告秒，reserved=0；这是账号级差值，不冒充该Notebook独立账单。平台请求窗口10000s，未提供独立effective-window字段。模型服务7个已观测进程均退出，剩余PID=[]，最终服务running/waiting gauges归零；四个Worker与chroot清理均确认。

GPU原始ZIP3256396bytes，CRC有效，SHA72030f1833ee6a8588087836bf281ae3aafae4c5a327b4f1d5651482aed7bea6。CPU原始ZIP992678bytes，SHA dd6aa5f88bc57c698a6e566843610bad1c7b2fdb73cf106c0ca58ceaa7058433。位置与下载证据见RAW_ARCHIVES.json/read_observations；原始Patch、HTTP轨迹、真实TaskResult/JUnit及评测资料留在受控private-evidence，不复制到公开PR。

## Q1–Q17

1. **是，最终实际载荷端到端CPU PASS。** CPU_END_TO_END_ACCEPTANCE.json绑定140305458/v1、原始ZIP及共享载荷SHA；启动自解包SOURCE目录，非开发树。
2. **是，两次历史遗漏在同一生产入口实际覆盖。** 全pins字节比对、CPU_GATE_PIN及真实native_baseline惰性导入已执行，GPU对应链路也成功。历史GPU01/GPU02失败保持原样。
3. **目录冲突消失。** CPU/GPU实际Worker均完成；被动HTTP observer只创建可信侧兄弟目录，保留Runner独占Agent目录创建语义，事件原字节迁回。
4. **是，Baseline→Agent→Patch→Verifier→JUnit→Cleanup连续通过。** CPU是自建合成Agent任务，真实两题只用于身份和空Patch基线；脚本化结果不计入GPU修复率。
5. **是，实际4×L4。** GPU_EXECUTION_RECORD.json、safe_evidence/results/GPU_DEVICES.json。
6. **是，真实加载并推理。** 八文件SHA、TP4/vLLM配置、后台日志索引、服务身份和四组真实HTTP轨迹；CPU模拟文件未进入GPU路由。
7. **106请求、106响应，全部200及完整usage。** prompt840263、completion20704、total860967tokens。A50请求/366740tokens，B56请求/494227tokens。AGENT_BEHAVIOR_METRICS.json及ACTUAL_OUTPUT_TESTS.log。
8. **四次均实际运行并完成。** ABBA_RESULTS.json顺序9425A→9425B→14786B→14786A；各自独立Worker/chroot/ADK Session/Workspace/Verifier/日志，复用服务而不共享对话。
9. **NoEGV：9425false，14786true。** NATIVE_VERIFIER_RESULTS.json，真实JUnit分别1failure/0error和9passed。
10. **Action-First：两题均true。** 真实JUnit分别1passed、9passed，均0error。
11. **没有一致更早。** 9425只有B实际修改生产源码（138.953s）；14786B30.341s、A29.648s。事件区间和文件哈希见AGENT_BEHAVIOR_METRICS.json。
12. **提交/结束更好，总tokens与工具更多。** 成本表与TRAJECTORY_REVIEW.json保留全部四组；不能用非空诊断Patch替代有效修复，也不能用局部断言替代Native resolved。
13. **A14786有重复提交及4次提交后调用。** 完全相同搜索命令proxy各0；A9425有一次相同read响应proxy。相同pytest表面重复在A14786实际经历测试输入变化，不定为无进展重复。完整隐藏环境恒等无法证明，保留proxy限制。
14. **Agent689.210s，其他代码700.857s。** RESOURCE_ACCOUNTING.json分解；独立GPU账单与峰值显存UNKNOWN，账号配额差不能作为账单。
15. **没有终止性基础设施阻断。** 首个原生失败是9425A的目标断言仍失败；过程的提前停止证据是context guard的15881输入/33289reserved拒绝，且无生产修复。14786A同类停止发生于已有正确Patch之后。广pytest环境错误单独记录，不算原生任务算法失败。
16. **候选、任务及历史完整。** NoEGV/Action/Full ZIP及成员SHA、pins、Task/Issue/Base/Snapshot/Overlay、300/60/120、生成参数及ABBA不变。源码commit9cac931，载荷冻结de87e22，派发前CPU门禁1d24bbc；CPU后共享生产代码/ZIP未变。只有本轮新目录变更；零新正式Submission。
17. **获得足以指导下一步的初步真实算法证据，但不能证明总体优势。** 本次支持保留Action-First做独立任务确认，尤其关注避免“只有诊断没有生产修改”和提交后立即结束。第一编辑时间并非普遍改善，总tokens并未下降。两道FastAPI、每臂每题一次及首轮冷缓存/顺序效应限制外推。本轮不含Full/EGV，不能解释Full0.12或宣称EGV有效。不得热修复Prompt后重跑本冻结实验。

## 审计限制和执行记录

一个CPU SaveKernel、一个GPU SaveKernel，没有第二次GPU03请求、CPU Mock混入GPU或正式Submission。保留初始UNKNOWN_STOP，后续只读确认身份/源码/版本。运行中的日志流及输出接口各返回404一次，已停止该接口重试，之后按正式完成版本回收；没有据此重新保存。原始状态查询与网络延迟记录全部保留。

本地预检23PASS；另一次派发前9项子集PASS。真实输出6项离线一致性检查PASS。首次离线测试错误地要求每次成功提交都带可选activity文本；A14786没有该文本但有原生ADK成功响应、context.patch_submitted状态和真实补丁。保留ACTUAL_OUTPUT_TESTS_01_FAILED.log，修正为实际回调/响应证据后通过，未修改原始数据或把失败回填成功。
