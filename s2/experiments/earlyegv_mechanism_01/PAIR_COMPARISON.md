# 预注册两任务配对结果

S2-T500-EARLYEGV-MECHANISM-01；Notebook wudangdexiaodoashi/gemma4-s2-earlyegv-mechanism-01，版本1，COMPLETE。
4次真实Gemma运行全部完成；0 unknown、0 not_run、0实验STOP；两组各2题官方resolved=true。
配对：两组都成功2题；A独胜0、B独胜0；配对成功差值0。两题为确定性选择的公开样本，不是总体修复率估计或排行榜分数。

|任务/臂|官方resolved / Phase2|首次目标源码变更秒|Agent秒|Worker秒|计费工具 / 原始工具|官方LLM / HTTP|收到HTTP Token|显式submit次数|EGV|
|---|---|---:|---:|---:|---|---|---:|---:|---:|
|rich_3676 A|true / 21 passed, 1 skipped|259.63|491.456|521.544|60 / 60|61 / 67|391509|0|0|
|rich_3676 B|true / 21 passed, 1 skipped|164.64|473.569|503.503|60 / 61|62 / 68|390688|1|0|
|fastapi_14492 B|true / 2 passed|39.63|209.495|238.480|27 / 30|31 / 33|185922|3|0|
|fastapi_14492 A|true / 2 passed|108.56|123.405|152.305|23 / 24|25 / 26|146946|1|0|

首次变更时间来自插件工具完成/源码哈希快照，是实际写入时刻的观测上界。
Rich首次仅增加Stack字段，不能当成已经完成修复；三处最终候选变更全部具备的时刻为A385.36秒、B193.76秒。
FastAPI目标是docs_src中的可执行文档示例，首次改动B39.63/A108.56；fastapi库核心生产代码均未改动。
自动提取器原始descriptive.json只按rich/或fastapi/识别生产文件，因此FastAPI原字段为null；人工目标分类新增于ANALYSIS_MEASUREMENTS.json，原字段和原始证据未改写。

|汇总|A|B|B−A|
|---|---:|---:|---:|
|官方成功任务|2|2|0|
|Agent总秒|614.860|683.063|+68.203（+11.09%）|
|Worker总秒|673.849|741.983|+68.134（+10.11%）|
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

- [rich_3676 A：原生结果](results/gpu01/runs/01-rich_3676-A/official_result.json)、[Phase2](results/gpu01/runs/01-rich_3676-A/official_phase2.log)、[JUnit](results/gpu01/runs/01-rich_3676-A/phase2.junit.xml)、[Patch](results/gpu01/runs/01-rich_3676-A/latest.patch)、[逐工具事件](results/gpu01/runs/01-rich_3676-A/posthoc/tool_events.json)。
- [rich_3676 B：原生结果](results/gpu01/runs/02-rich_3676-B/official_result.json)、[Phase2](results/gpu01/runs/02-rich_3676-B/official_phase2.log)、[JUnit](results/gpu01/runs/02-rich_3676-B/phase2.junit.xml)、[Patch](results/gpu01/runs/02-rich_3676-B/latest.patch)、[逐工具事件](results/gpu01/runs/02-rich_3676-B/posthoc/tool_events.json)。
- [fastapi_14492 B：原生结果](results/gpu01/runs/03-fastapi_14492-B/official_result.json)、[Phase2](results/gpu01/runs/03-fastapi_14492-B/official_phase2.log)、[JUnit](results/gpu01/runs/03-fastapi_14492-B/phase2.junit.xml)、[Patch](results/gpu01/runs/03-fastapi_14492-B/latest.patch)、[逐工具事件](results/gpu01/runs/03-fastapi_14492-B/posthoc/tool_events.json)。
- [fastapi_14492 A：原生结果](results/gpu01/runs/04-fastapi_14492-A/official_result.json)、[Phase2](results/gpu01/runs/04-fastapi_14492-A/official_phase2.log)、[JUnit](results/gpu01/runs/04-fastapi_14492-A/phase2.junit.xml)、[Patch](results/gpu01/runs/04-fastapi_14492-A/latest.patch)、[逐工具事件](results/gpu01/runs/04-fastapi_14492-A/posthoc/tool_events.json)。
