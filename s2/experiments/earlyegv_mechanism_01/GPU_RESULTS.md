# 实际GPU结果与Q1–Q15

已完成唯一一次Notebook保存执行，版本1 COMPLETE。四臂均官方resolved=true；0 EGV调用，0可观察双Agent修复闭环。
A/B各2题成功，配对差值0；B的Agent总耗时+11.09%、HTTP Token+7.09%，显式提交任务1/2→2/2，但Rich诊断残留1→5。
结论：基础设施Go，当前证据不支持扩大双Agent效能实验；更早源码修改/部分收尾变化是较窄的Main工作流信号。

|任务/臂|官方resolved / Phase2|首次目标源码变更秒|Agent秒|Worker秒|计费工具 / 原始工具|官方LLM / HTTP|收到HTTP Token|显式submit次数|EGV|
|---|---|---:|---:|---:|---|---|---:|---:|---:|
|rich_3676 A|true / 21 passed, 1 skipped|259.63|491.456|521.544|60 / 60|61 / 67|391509|0|0|
|rich_3676 B|true / 21 passed, 1 skipped|164.64|473.569|503.503|60 / 61|62 / 68|390688|1|0|
|fastapi_14492 B|true / 2 passed|39.63|209.495|238.480|27 / 30|31 / 33|185922|3|0|
|fastapi_14492 A|true / 2 passed|108.56|123.405|152.305|23 / 24|25 / 26|146946|1|0|

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

- [rich_3676 A：原生结果](results/gpu01/runs/01-rich_3676-A/official_result.json)、[Phase2](results/gpu01/runs/01-rich_3676-A/official_phase2.log)、[JUnit](results/gpu01/runs/01-rich_3676-A/phase2.junit.xml)、[Patch](results/gpu01/runs/01-rich_3676-A/latest.patch)、[逐工具事件](results/gpu01/runs/01-rich_3676-A/posthoc/tool_events.json)。
- [rich_3676 B：原生结果](results/gpu01/runs/02-rich_3676-B/official_result.json)、[Phase2](results/gpu01/runs/02-rich_3676-B/official_phase2.log)、[JUnit](results/gpu01/runs/02-rich_3676-B/phase2.junit.xml)、[Patch](results/gpu01/runs/02-rich_3676-B/latest.patch)、[逐工具事件](results/gpu01/runs/02-rich_3676-B/posthoc/tool_events.json)。
- [fastapi_14492 B：原生结果](results/gpu01/runs/03-fastapi_14492-B/official_result.json)、[Phase2](results/gpu01/runs/03-fastapi_14492-B/official_phase2.log)、[JUnit](results/gpu01/runs/03-fastapi_14492-B/phase2.junit.xml)、[Patch](results/gpu01/runs/03-fastapi_14492-B/latest.patch)、[逐工具事件](results/gpu01/runs/03-fastapi_14492-B/posthoc/tool_events.json)。
- [fastapi_14492 A：原生结果](results/gpu01/runs/04-fastapi_14492-A/official_result.json)、[Phase2](results/gpu01/runs/04-fastapi_14492-A/official_phase2.log)、[JUnit](results/gpu01/runs/04-fastapi_14492-A/phase2.junit.xml)、[Patch](results/gpu01/runs/04-fastapi_14492-A/latest.patch)、[逐工具事件](results/gpu01/runs/04-fastapi_14492-A/posthoc/tool_events.json)。

这些是两题公开研究任务的官方原生Verifier结果，不是Kaggle正式Public Score。
