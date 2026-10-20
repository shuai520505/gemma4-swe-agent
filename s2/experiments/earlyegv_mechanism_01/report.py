"""Publish this completed study's measured results and bounded manual judgments."""
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def load(name):
    return json.loads((HERE/name).read_text(encoding='utf-8'))


def emit(name,text):
    with (HERE/name).open('x',encoding='utf-8') as file:file.write(text)


if __name__=='__main__':
    data=load('ANALYSIS_MEASUREMENTS.json')
    rows=data['records'];totals=data['arm_totals']
    links=lambda r: r['evidence_root']
    table=['|任务/臂|官方resolved / Phase2|首次目标源码变更秒|Agent秒|Worker秒|计费工具 / 原始工具|官方LLM / HTTP|收到HTTP Token|显式submit次数|EGV|',
           '|---|---|---:|---:|---:|---|---|---:|---:|---:|']
    for r in rows:
        phase='21 passed, 1 skipped' if r['instance_id'].startswith('rich') else '2 passed'
        table.append(f"|{r['instance_id']} {r['arm']}|true / {phase}|{r['first_target_source_edit_seconds']:.2f}|{r['Agent_seconds']:.3f}|{r['Worker_seconds']:.3f}|{r['counted_tools']} / {r['actual_tool_starts']}|{r['native_LLM_calls']} / {r['HTTP_dispatches']}|{r['HTTP_received_only_tokens']['total_tokens']}|{r['successful_submit_calls']}|0|")
    table='\n'.join(table)
    refs='\n'.join(f"- [{r['instance_id']} {r['arm']}：原生结果]({links(r)}/official_result.json)、[Phase2]({links(r)}/official_phase2.log)、[JUnit]({links(r)}/phase2.junit.xml)、[Patch]({links(r)}/latest.patch)、[逐工具事件]({links(r)}/posthoc/tool_events.json)。" for r in rows)
    emit('PAIR_COMPARISON.md',f'''# 预注册两任务配对结果

S2-T500-EARLYEGV-MECHANISM-01；Notebook wudangdexiaodoashi/gemma4-s2-earlyegv-mechanism-01，版本1，COMPLETE。
4次真实Gemma运行全部完成；0 unknown、0 not_run、0实验STOP；两组各2题官方resolved=true。
配对：两组都成功2题；A独胜0、B独胜0；配对成功差值0。两题为确定性选择的公开样本，不是总体修复率估计或排行榜分数。

{table}

首次变更时间来自插件工具完成/源码哈希快照，是实际写入时刻的观测上界。
Rich首次仅增加Stack字段，不能当成已经完成修复；三处最终候选变更全部具备的时刻为A385.36秒、B193.76秒。
FastAPI目标是docs_src中的可执行文档示例，首次改动B39.63/A108.56；fastapi库核心生产代码均未改动。
自动提取器原始descriptive.json只按rich/或fastapi/识别生产文件，因此FastAPI原字段为null；人工目标分类新增于ANALYSIS_MEASUREMENTS.json，原字段和原始证据未改写。

|汇总|A|B|B−A|
|---|---:|---:|---:|
|官方成功任务|2|2|0|
|Agent总秒|{totals['A']['Agent_seconds']:.3f}|{totals['B']['Agent_seconds']:.3f}|+68.203（+11.09%）|
|Worker总秒|{totals['A']['Worker_seconds']:.3f}|{totals['B']['Worker_seconds']:.3f}|+68.134（+10.11%）|
|计费工具|83|87|+4|
|原始工具开始事件|84|91|+7|
|官方LLM调用|86|93|+7|
|HTTP模型dispatch|93|101|+8|
|完整收到的HTTP Token|538455|576610|+38155（+7.09%）|
|有成功显式提交的任务|1/2|2/2|+1题|
|成功submit调用次数|1|4|B中含重复提交，不能当成4题成功|
|最终Patch无关诊断文件|1|5|+4|
|EGV调用 / 有效EGV闭环|0 / 0|0 / 0|无机制证据|

官方total_tokens=0原样保留；成本比较使用http_lifecycle真实响应usage，194个请求均有完整响应用量，0取消/0补零。
模型调用、工具计费、原始工具事件、HTTP dispatch并非同一计数。HTTP包含压缩等额外模型请求。
ADK按角色收到的Main Token：A517318、B554317；与全HTTP合计口径不同，不重复相加。
EGV无任何调用及usage记录，记N/A；并非将缺失响应usage填0。

{refs}
''')
    emit('EGV_BEHAVIOR_AUDIT.md', '''# EGV行为审计：未观察到自主委派

四份nested_audit.jsonl中，egv_verifier工具开始事件、子Agent模型开始事件和子Agent工具事件均为0。
HTTP Main工具schema请求数依次为61、62、31、25，共179；全部包含egv_verifier。
其余15个HTTP请求为不带工具schema的压缩等请求，不误算为子Agent。
因此不是“schema完全缺失”的已知CPU兼容故障；真实Gemma在本次合法工具选择中没有委派。
子Agent权限和共享预算的CPU证据保留，但不能声称本轮GPU已实际压力验证子Agent取消/副作用/500秒边界。

|问题|A两题|B两题|
|---|---|---|
|实际EGV调用|0|0|
|EGV真实行为断言|无|无|
|可操作EGV反证 / 交付 / Main处理|0 / 0 / 0|0 / 0 / 0|
|EGV引起的Main生产修订 / 成功复验|无|无|
|有效EGV闭环率|分母为0，null|分母为0，null|
|首次委派、委派预算、Patch前后位置|N/A|N/A|

无可评级的EGV反证，证据等级为N/A，不能把模型总结或Main自己的探针记作EGV结果。

Main的直接行为需要另行区分：

- Rich B：nested_audit 35–40创建并运行add_note探针，79–92对比标准traceback；95–104完成三处生产改动。
  之后多个reproduction/test_notes_capture脚本失败来自错误API调用或脚本假设，Main修改的是诊断脚本，未再修改生产文件。
  这不是“EGV反证→Main修订→成功复验”闭环。打印实际渲染有Level2行为信息；仅打印__notes__类型/提取字段为Level3。
- Rich A：179–192的自编探针先用无效show_traceback参数失败，再修正脚本并打印；直接将__notes__设为字符串，未覆盖add_note产生列表的常规路径。
  B在223–224真实显示Python3.12的__notes__为list。A对列表notes的兼容性是未实测风险，不能因21项原生测试通过就宣称所有契约已覆盖，也不能把尚未实测的风险重写为官方失败。
- FastAPI B：43–48按Issue将本地测试期望同步为Apache-2.0后执行pytest，两条断言测试通过，包含既有/items/行为。
  这是Main的实际验证，不是EGV；改变后的本地测试不能冒充原封不动的回归套件。最终官方提交过滤了测试文件，原生Phase2在新sandbox独立通过。
- FastAPI A：没有Agent主动测试命令，只有源码/文档搜索和diff；独立原生Phase2随后通过。

来源限制：Rich的import_audit记录工作区rich.traceback路径、源码SHA和模块代码执行，但模块被执行本身不证明行为断言通过。
FastAPI B pytest命令对应import_audit/68a289dfe35e4d61a3499c5ccb61f3c5/2453-exit.json，确认cwd、sys.path及工作区fastapi包。
冻结观察前缀仅fastapi，未单独记录被修改docs_src模块的__file__；测试import源码、工作目录、目标响应和最终Native Phase2提供强间接来源，不能伪造直接docs_src来源记录。

四臂get_status次数均为0，无证据证明模型按软检查点主动查询剩余预算。
0委派不能单凭本样本证明模型永远不会协作；两题可以被Main完成，且允许合理跳过委派。但本实验没有验证H1独立反证或H2反馈修复，也不支持H3净收益提升。
''')
    emit('PATCH_TIMING_AUDIT.md', '''# 源码改动与探查时序

时间均为nested插件工具完成时间，相对本臂Agent开始；不同于旧audit_result按工具意图或任意write_file给出的first_edit_action。
不把诊断脚本创建计为生产编辑，不把部分字段变更计为完整正确修复。

|任务|A首次直接读取目标|B首次直接读取目标|A首次目标改动|B首次目标改动|编辑前工具 A/B|
|---|---:|---:|---:|---:|---:|
|rich_3676|13.81|12.36|259.63|164.64|39 / 23|
|fastapi_14492（文档示例源码）|77.99|24.20|108.56|39.63|19 / 6|

Rich证据：A nested行12首次读取；160添加字段、164复制notes、172完成渲染，最后385.36秒。
B行12读取；96字段、100复制、104渲染，最后193.76秒。首改B提前94.99秒；三处候选齐备提前191.60秒。
两份候选都通过既定Phase2；这不排除未覆盖输入风险。A按字符串、B按列表处理notes，生产改动本身不同，不能把先后时间等同于同等全语义正确性。

FastAPI A行52读取、80编辑；B行20读取、28编辑，B提前68.93秒。
最终两份Patch字节一致，唯一更改是可执行示例license identifier从MIT变为Apache-2.0；这是Issue明确要求，不是FastAPI库核心功能实现。

|观察|Rich A|Rich B|FastAPI A|FastAPI B|
|---|---:|---:|---:|---:|
|工具返回status=error|7|4|5|3|
|同一文件版本、相同内容的重复read|2|1|1|1|
|工作区不变时的相同命令重复|3|0|0|0|
|read_file非法/未知参数键|3|0|0|0|

以上重复是可复核的描述计数，不自动判断都无价值；源码变化后的合理重读排除。
grep无匹配可能是正常反证，不能与错误脚本、环境错误混为一类。
A Rich行107/111/119使用start_line加多余引号的键，返回默认文件头；重复内容位于111/119。
A行99/127反复grep class Stack、139反复搜索不存在的__rich_yield__，没有工作区增量信息。
B虽减少早期无增量定位，却在194秒后反复写诊断、运行print-only探针及错误API；源码早改没有自动转化为更低总成本。

原生A Rich于491.46秒触发60次工具上限；不是500秒时间超时。
B Rich60次计费工具后仍能免费submit，正常结束473.57秒。FastAPI B209.49秒，反而比A123.40秒慢86.09秒。
没有任何本轮Agent触发500秒截止，不能声称本轮真实GPU已重新测得500秒硬截止；该精确边界仍由冻结CPU500.100秒证据支持。

独立测量在ANALYSIS_MEASUREMENTS.json；四份posthoc/tool_events.json和.csv提供完整逐事件参数/结果/哈希变更及原始行指针。
''')
    emit('CLOSURE_AND_SUBMIT_AUDIT.md', '''# 收尾与提交审计

|任务/臂|显式成功submit|首次成功完成秒|fallback|最终无关诊断文件|
|---|---:|---:|---|---:|
|Rich A|0|N/A|是|1|
|Rich B|1|457.13|否|5|
|FastAPI B|3|135.08|否|0|
|FastAPI A|1|122.89|否|0|

按任务计的显式提交比例A1/2、B2/2；不可把B的4次调用当4题成功。
Rich B行239–244做git diff并成功提交；A工具预算耗尽，无submit，Harness捕获工作树。
FastAPI B行91–96做git diff --check并提交，107–108、119–120重复提交。
三个submit返回完全相同391字节/1文件，相关源码在39.63秒后未再修改；无证据证明后两次提交有新增修复价值。
首次成功submit到Agent结束B约74.42秒，A约0.51秒。最后一次B提交后还约17.15秒才终止；不能把submit工具返回当成会话已经结束。

诊断污染：

- Rich A最终包含reproduce_notes.py。
- Rich B最终包含output.txt（ANSI渲染输出）、repro.py、reproduction.py、standard_traceback.py、standard_traceback_multi.py，另有真实生产rich/traceback.py。
- Rich B工作区还有test_notes_capture.py；官方过滤后未进入最终Patch。
- FastAPI B修改了本地tests/test_tutorial/test_metadata/test_tutorial001_1.py，运行其测试；官方submit只捕获文档示例源码，测试修改不在最终391字节Patch。

这不是研究者修改Verifier或评分测试：原生Phase2在独立sandbox按固定Task测试补丁执行，JUnit/命令/原始TaskResult均保存。
但B的本地测试已被改动，应据实披露，不称为“未经修改的既有测试全通过”。
四臂均未观察到删除自己诊断文件的动作。B提升了观察到的显式提交任务比例，但没有达成诊断清理目标；Rich的污染文件从1增加到5。
原生21 passed/1 skipped或2 passed不能消除这些Patch卫生问题，也不能证明未运行的所有旧行为无回归。
''')
    emit('GPU_RESULTS.md',f'''# 实际GPU结果与Q1–Q15

已完成唯一一次Notebook保存执行，版本1 COMPLETE。四臂均官方resolved=true；0 EGV调用，0可观察双Agent修复闭环。
A/B各2题成功，配对差值0；B的Agent总耗时+11.09%、HTTP Token+7.09%，显式提交任务1/2→2/2，但Rich诊断残留1→5。
结论：基础设施Go，当前证据不支持扩大双Agent效能实验；更早源码修改/部分收尾变化是较窄的Main工作流信号。

{table}

|问题|实际回答与证据|
|---|---|
|Q1 GPU启动/版本|是，wudangdexiaodoashi/gemma4-s2-earlyegv-mechanism-01 / v1，SAVE_RAW_RESPONSE.json和终态观察。|
|Q2 四运行完成|4/4，results/gpu01/batch_gate.json，not_run为空，无STOP。|
|Q3 Rich A/B|true/true；各21 passed、1 skipped；原生退出0。|
|Q4 FastAPI A/B|true/true；各2 passed；原生退出0。|
|Q5 真EGV调用|没有，四条nested轨迹均0；179个Main schema请求全部包含AgentTool。|
|Q6 EGV反证|0，无可评级EGV证据。|
|Q7 Main处理EGV反证|未发生；Main自身改诊断脚本不算EGV引起生产修订。|
|Q8 EGV闭环复验|未发生，分母0、闭环率null；Main有独立直接验证，详见EGV_BEHAVIOR_AUDIT。|
|Q9 B较早改源码|两题观察到较早：Rich首改提前94.99秒、FastAPI示例提前68.93秒；不是完整正确性的独立保证。|
|Q10 显式提交比例|观察值A1/2、B2/2；FastAPI B另有两次无新Patch的重复提交。|
|Q11 成本|A/B收到HTTP Token538455/576610；计费工具83/87；Agent总614.860/683.063秒，Worker673.849/741.983秒。|
|Q12 回归/残留|既定Phase2无失败；未运行输入仍未知；Rich残留A1/B5。B FastAPI本地测试被同步修改，最终Patch不含该测试。|
|Q13 协议/STOP|按ABBA完整执行，无实验STOP/重跑/换题/热修；本地JSON与执行JSON仅CRLF/LF表示差异单独披露，实际执行哈希匹配预封存值。|
|Q14 正式57402336|收尾实际查询2026-10-20T08:35:29.568460+00:00：PENDING、Public Score=null、无错误描述；S0为COMPLETE/0.13。预检和收尾快照分别保存于FORMAL_SCORE_STATUS.json与FORMAL_SCORE_STATUS_FINAL.json，未持续轮询或发起新提交。|
|Q15 继续/改变方向|不建议直接扩大当前双Agent版本至8/16运行；先分离Main早编辑/收尾信号，避免把未发生的EGV协作当收益。新实验须另行预注册和授权。|

## 执行与证据完整性

实际4×NVIDIA L4、TP4、CUDA12.8、driver580.178.04、torch2.10.0+cu128、vLLM0.19.1；核心包版本与冻结Wheelhouse一致。
模型8文件、模型wheel和任务wheel、230项执行源码绑定、A/B ZIP/成员、任务Issue/base/snapshot及ABBA顺序核验通过。
所有194个模型HTTP请求都有唯一request_id和response_received终态，usage完整；0取消、0超时传输、0finish_length。
本轮没有实际压力触发取消路径；不能把旧CPU取消证据说成本轮GPU取消实测。
每臂结束3个连续server idle快照、worker/sandbox清理通过，最终7个已跟踪模型服务PID无残留且无强制kill。
后台日志及请求生命周期保存；未取得请求级abort确认，也没有虚构此类确认。
JUnit在原生sandbox停止前取得，XML SHA与capture记录一致；原始resolved/test_exit_code/total_tokens字段不改写。

10000秒为实际SaveKernel请求并被平台接纳的配置；状态API不独立回显批准超时，runtime未暴露额外timeout字段。
执行器从容器PID1创建计时，运行前及每臂前均保留全部剩余slot和900秒收尾；四臂完整完成。
日志到最终证据导出约2064.55秒，低于10000；不声称实测了10000秒平台硬截止。
账户报告配额增加4150.070秒，剩余83044.286；单位是原始Duration报告秒，非GPU设备小时账单或每臂独立收费。

原始下载一次网络截断后，仅分段恢复同一个完成版本输出，未重跑任何模型任务。
42,305,958字节原始ZIP SHA256：d51735ad43a2d6318c1ec7fb10bd607b7ba9906d268b3b87924d547445f08b68。
RAW_COLLECTION.json验证根与4个嵌套归档的CRC/每文件清单SHA；results/gpu01/raw.zip保留原始完整字节。
source未展开成可混淆的新本地工作树；原始ZIP内包含实际执行source，独立源码绑定审核通过。

本地AUTHORIZED_PROTOCOL.json是Windows CRLF，执行载荷为预先声明的规范LF序列化；语义完全一致。
执行SHA86f5ce2149fbb046752173aa630701966cc4a54eb8480120f3f643dac2947df4从保存前就封存在EXECUTION_BUILD_MANIFEST与授权记录，并与实际源文件、batch_gate一致。
初次审计逐字节比较本地文档副本失败的事实保留于PROTOCOL_REPRESENTATION_AUDIT.json；未改动任何原件以隐藏差异。
这不是候选/执行源码/模型/任务漂移；也不把两种换行文件声称为字节相同。下载复本/分段留在本机download目录，Git保留canonical原始ZIP和传输SHA日志。

{refs}

这些是两题公开研究任务的官方原生Verifier结果，不是Kaggle正式Public Score。
''')
    emit('EXPERIMENT_DECISION.md', '''# Go/No-Go

**CPU Feasibility Go保留；GPU资源/基础设施Go，已完成；本次授权4/4履行，额外GPU与正式提交未授权；当前双Agent扩样No-Go。**

H1独立EGV证据：未观察到（0调用）。H2反证修复闭环：未观察到（率null）。
H3净竞争收益：两组各2题通过，B时间/Token更高；本次无正向完整任务成功差异，不能晋级为双Agent优越证据。
也不能据两题断言真实Gemma在任何任务都不会委派，或此架构永远无效；文档一行修复尤其可能合理选择直接路径。

确实观察到的Main工作流变化：两题较早修改目标源码；Rich较早形成三处完整候选并显式提交，避免A的工具耗尽fallback。
负面：Rich仍耗尽60计费工具，B没有get_status；诊断增多且不清理；FastAPI重复相同submit并在首次成功后继续约74秒；总成本高。
不能把两项联合策略分别认作因果贡献，也不能用早写字段替代正确修复。

最低成本下一步（只建议，不执行）：

1. 暂停直接8任务/16运行双Agent扩样。冻结本轮真实失败模式与正向局部行为，不因0EGV重跑这两题或改写旧Prompt。
2. 若继续收尾研究，另建独立候选/预注册，单独检验成功submit后立即文本终止、相同Patch不重复提交、仅清理自己诊断文件；不同时再改Agent数量/生成参数。
3. 若研究EGV协作本身，先用未暴露且存在可证伪验证不确定性的预注册任务设计，明确可观察委派机会；或在官方声明式支持范围单独研究可靠角色调度。
   先通过CPU角色/预算兼容，再申请小规模公平配对；不靠机械强制调用或本题专用答案制造机制成功。

本轮未启动LoRA、未新增候选/Prompt调参、未正式提交榜单。正式57402336的本轮查询仍无成绩，不能据这些公开任务结果宣称超过S0的0.13。
''')
    # Publish annotations explicitly stating absence, never fabricated tool pointers.
    with (HERE/'MECHANISM_ANNOTATIONS.json').open('x',encoding='utf-8') as f:
        json.dump(dict(EGV_annotations=[],qualified_EGV_counterevidence=0,delivered=0,handled=0,closed=0,
            closed_loop_rate=None,evidence_level='N/A: no EGV invocation',
            manual_review_scope='All four tool timelines, all production/example diffs, diagnostic scripts and test returns; no reference repair read and no additional tests run.',
            limitations=['Rich A list-notes behavior untested','docs_src target module not included in frozen fastapi import prefix','two selected tasks/one seed cannot establish population superiority']),f,indent=2)
    print('Published measured paired, EGV, timing, closure, decision and Q1-Q15 reports.')
