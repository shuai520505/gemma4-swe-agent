"""Build additive status reports from this read-only snapshot, never a candidate."""
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
EARLY = HERE.parents[1]


def read(name):
    return json.loads((HERE / name).read_text(encoding='utf-8'))


def emit(name, obj):
    text = obj if isinstance(obj, str) else json.dumps(obj, indent=2, ensure_ascii=False) + '\n'
    target = HERE / name
    if target.exists():
        raise FileExistsError(target)
    target.write_text(text, encoding='utf-8')


if __name__ == '__main__':
    rows = read('submissions_raw.json')
    scores = {str(r['ref']): r for r in rows['result']}
    s2, s0 = scores['57402336'], scores['57261002']
    assert s2['status'] == 'PENDING' and s2['publicScore'] is None
    assert s0['status'] == 'COMPLETE' and s0['publicScore'] == '0.13'
    emit('FORMAL_SCORE_STATUS_LATEST.json', {
        'query_started_at_utc': rows['started_at_utc'], 'query_finished_at_utc': rows['finished_at_utc'],
        'competition': 'gemma-4-developer-agent', 'submissions': [s2, s0],
        'new_submission_requests': 0, 'score_difference': None,
        'diagnostics_available': 'Only native ListSubmissions fields. No scorer log, queue position or scoring-start timestamp returned.',
        'interpretation': 'PENDING is the current API value; neither elapsed time nor totalBytes=0 establishes failure. No new score.',
        'raw_evidence': ['wire_ListSubmissions.json', 'submissions_raw.json'],
    })
    emit('FORMAL_SCORE_STATUS_LATEST.md', f'''# 正式评分快照

实际查询结束：{rows['finished_at_utc']}（北京时间 2026-10-20 14:35:46）。
API：competition_submissions / ListSubmissions；HTTP 200。没有新增提交请求。

| 候选 | Submission ID | 官方提交时间 UTC | API 状态 | Public Score | errorDescription |
|---|---|---|---|---|---|
| S0 | 57261002 | {s0['date']} | COMPLETE | 0.13 | null |
| 冻结 S2-T500 | 57402336 | {s2['date']} | PENDING | null | null |

S2-T500 尚不能与 0.13 作分数差值比较。EarlyEGV 没有正式成绩，也没有真实 Gemma 运行结果。
API 另返回 totalBytes=0、fileName、提交描述、提交者、队伍及保存版本 URL；完整原生字段在
[submissions_raw.json](submissions_raw.json)，未加工 HTTP 响应在 [wire_ListSubmissions.json](wire_ListSubmissions.json)。
没有返回 scorer 日志、错误堆栈、评分开始时刻、排队位置或任务进度。
不能凭持续时间、totalBytes=0 或用户界面的 Scoring 字样推断失败。
rich_3471 的单题 resolved=true 不是榜单成绩。

历史快照保持原样；这些文件是新的时间戳目录内观察，不替换旧状态文件。
''')
    wire = read('wire_GetAcceleratorQuotaStatistics.json')
    gpu = wire['response']['gpuQuota']
    number = lambda key: Decimal(gpu[key][:-1])
    allowed, used, reserved = [number(k) for k in ('totalTimeAllowed', 'timeUsed', 'timeReserved')]
    remaining = allowed - used - reserved
    threshold = Decimal(20600)
    statuses = read('notebook_statuses.json')
    counts = Counter(v.get('result', {}).get('status', 'UNKNOWN') for v in statuses.values())
    emit('GPU_QUOTA_LATEST.json', {
        'queried_at_utc': wire['queried_at_utc'], 'raw_http': wire,
        'sdk_formatted': read('quota_raw.json')['result']['sdk'],
        'duration_unit': 'seconds in raw protobuf Duration JSON, not device-hours or guaranteed Notebook wall-seconds',
        'total_reported_seconds': str(allowed), 'used_reported_seconds': str(used),
        'reserved_reported_seconds': str(reserved), 'remaining_reported_seconds': str(remaining),
        'required_reported_seconds': str(threshold), 'surplus_reported_seconds': str(remaining - threshold),
        'quota_gate': 'GO', 'quota_reset_since_prior_snapshot': False,
        'refresh_at_utc': wire['response']['quotaRefreshTime'],
        'malformed_sdk_root_cause': 'kagglesdk 0.1.35 TimeDeltaSerializer uses timedelta.seconds (drops days), and emits malformed fractional values; raw HTTP is valid.',
        'current_accelerator_allocatability': 'UNKNOWN', 'current_4xL4_allocatability': 'UNKNOWN',
        'prior_GPU_metadata_fresh_read': 'NvidiaL4, model version 2 and pinned Docker image; metadata is prior saved version, not live capacity.',
        'account_specific_session_window_seconds': None,
        'published_general_window_seconds': 43200,
        'published_general_window_evidence': 'Official Kaggle docs search index; direct open yielded no body. Not an account/machine-specific admission.',
        'notebook_status_scope': '165 saved own Notebooks enumerated; status endpoint reports latest saved session, not all interactive sessions.',
        'saved_status_counts': dict(counts), 'all_account_running_sessions_absent': None,
        'status_query_errors': dict(Counter('429' if '429' in v.get('error', '') else v.get('exception_type', 'ok') for v in statuses.values())),
        'gpu_resource_gate': 'NO_GO_PENDING_MACHINE_AND_SESSION_ADMISSION',
        'execution_authorization': 'NOT_GRANTED', 'GPU_started': False,
    })
    emit('GPU_QUOTA_LATEST.md', f'''# GPU 配额与资源快照

实际查询：{wire['queried_at_utc']}（北京时间 14:35:49）。原始 HTTP 200 响应见
[wire_GetAcceleratorQuotaStatistics.json](wire_GetAcceleratorQuotaStatistics.json)。

| 原始字段 | 数值（报告配额秒） |
|---|---:|
| totalTimeAllowed | {allowed} |
| timeUsed | {used} |
| timeReserved | {reserved} |
| 可用差额 | {remaining} |
| 冻结协议要求 | {threshold} |
| 高于要求的余量 | {remaining - threshold} |

**Quota Go。** 当前余额约为 24.221 个“报告配额小时”，约覆盖阈值 4.23 倍。
这些是平台 Duration 计账单位，不能当成 4×L4 的 GPU 设备小时或可用墙钟时间。
下一次重置为 2026-10-24 00:00 UTC（北京 08:00）。当前并未进入新周期：已用量与旧快照相同。

## 为什么此前显示只剩约 794 秒

当前 Kaggle 2.2.2 / kagglesdk 0.1.35 的原始 HTTP 总额是 **108000s**，不是21600s。
typed timedelta 为 1天6小时；SDK 的 TimeDeltaSerializer._to_dict_value 使用 `.seconds` 丢掉整天，
把总额错误格式化为21600s；小数又输出为 `20805.644.0s`。
这是可复现的客户端序列化缺陷，不是已经证明的配额新赠送或周期重置。
[SDK_DURATION_SERIALIZER.txt](SDK_DURATION_SERIALIZER.txt) 保存实际安装源码；
[DURATION_REGRESSION.log](DURATION_REGRESSION.log) 的3项离线测试验证 raw/typed 解释一致、
SDK错误重现、异常字符串拒绝及余额计算。没有修补 SDK，也没有“修正”历史响应。

## 设备、窗口与同时运行情况

- 最新只读 get_kernel 返回旧 Smoke 保存版本的 machineShape=NvidiaL4、模型v2、固定Docker摘要。
  历史真实轨迹证明那次获得4×L4；**当前4×L4即时可分配性 UNKNOWN**，未为探测而分配GPU。
- 官方 [Notebooks文档](https://www.kaggle.com/docs/notebooks) 搜索索引显示一般CPU/GPU窗口12小时，
  大于10000秒规划；直接打开页面未取得正文。它不能保证本账户当前L4保存版本获批的窗口。
- SDK可发送 `session_timeout_seconds` 整数和 `machine_shape`，但当前只读SDK没有实时机器配额/并发槽位/保存频率限制接口。
  请求参数可用不等于平台接受或容量可用；当前最大窗口、保存/启动限制均未完整核实。
- own saved-Notebook列表共165项、分页耗尽。77个成功状态查询均为终态（61 COMPLETE、16 ERROR）；
  其余88项未确认，其中83次429、4次其他HTTP错误、1次ValueError。没有重试风暴或持续轮询。
  关键Early CPU02、env01、旧GPU Smoke及正式打包Notebook均COMPLETE。
  该接口仅覆盖最近保存会话，不覆盖所有交互会话，故**全账户无并发运行 UNKNOWN**。
- GPU草案slug未出现在该保存Notebook清单；本轮未push/save/start。reserved=0不能证明没有任何运行会话。

**完整 GPU Resource No-Go（待机器及会话准入），不是配额不足。**
Execution Not Authorized。不能因为配额数字足够而把 UNKNOWN 字段填成已通过。
''')
    audit = read('READINESS_AUDIT.json')
    emit('RESOURCE_AND_EXECUTION_READINESS.json', {
        'generated_at_utc': datetime.now(timezone.utc).isoformat(),
        'CPU_gate': 'GO_REVALIDATED_FROZEN_EVIDENCE', 'quota_gate': 'GO',
        'GPU_resource_gate': 'NO_GO_PENDING_MACHINE_AND_SESSION_ADMISSION',
        'authorization': 'NOT_GRANTED', 'algorithm_evidence': 'NOT_TESTED_ON_REAL_GEMMA',
        'resource_window_seconds': 10000, 'general_documented_window_seconds': 43200,
        'agent_caps_total_seconds': 2000, 'worker_and_idle_slots_seconds': 6440,
        'model_startup_cap_seconds': 1200, 'installation_cap_seconds': 300,
        'baseline_check_caps_total_seconds': 600, 'finalization_seconds': 900,
        'planning_total_seconds': 9440, 'planning_slack_seconds': 560,
        'startup_admission_setup_elapsed_max_seconds': 1460,
        'quota_required_reported_seconds': '20600', 'quota_remaining_reported_seconds': str(remaining),
        'quota_gap_reported_seconds': '0', 'quota_surplus_reported_seconds': str(remaining - threshold),
        'GPU_runs_executed': 0, 'formal_submissions_sent': 0,
        'current_hardware_window_and_concurrency_guaranteed': False,
        'protocol_identity': 'S2-T500-EARLYEGV-MECHANISM-01', 'frozen_runs': audit['runs'],
        're_registration_needed_now': False,
        'future_authorized_build_needed': True,
        'future_build_rule': 'Do not rewrite frozen draft. Separate execution authorization and new execution build manifest/Notebook SHA binding original tasks/order/candidates/conditions. Material changes require amendment before inference.',
    })
    emit('EXECUTION_READINESS.md', '''# 两任务四运行：资源与待授权构建清单

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
''')
    emit('RESULTS.md', '''# 本轮结果与Q1–Q10

这是只读API/本地审计轮次，不是新的GPU实验或新算法候选。基线272c284；PR #7保持Draft。

| 问题 | 实际结论 | 证据 |
|---|---|---|
| Q1 57402336状态 | 2026-10-20 14:35:46北京时间，API PENDING，无错误描述 | FORMAL_SCORE_STATUS_LATEST.json、wire_ListSubmissions.json |
| Q2 S2-T500 Public Score | null | 同上 |
| Q3 与S0相比 | S0 COMPLETE/0.13；尚不能比较差值 | 同上 |
| Q4 GPU配额 | 原始总108000s、已用20805.644s、预留0s，余额87194.356报告配额秒；wire/typed可信，SDK格式化错误 | GPU_QUOTA_LATEST.*、SDK_DURATION_SERIALIZER.txt、DURATION_REGRESSION.log |
| Q5 四运行资源 | 数值配额门Go，缺口0、余量66594.356；10000s规划可容纳9440s预算；当前4L4即时容量/批准窗口/全账户会话未知，所以完整资源准入尚No-Go | RESOURCE_AND_EXECUTION_READINESS.json、EXECUTION_READINESS.md |
| Q6 Early SHA | 保持d1e815e770abbcc448325ad2a3c8785c62f6d3c63bc7f95700850748c048a487 | READINESS_AUDIT.json |
| Q7 相同预算 | A/B同500秒共享、60计费工具、命令120秒及相同生成参数/子Agent；仅Main Prompt不同 | READINESS_AUDIT.json、冻结协议与载荷绑定 |
| Q8 任务顺序 | rich_3676 A→B；fastapi_14492 B→A，未改变 | 同上 |
| Q9 Notebook准备 | 冻结草案/载荷/源码/CPU证据/隔离/清理保护完好，草案未出现在保存版本清单；仍不可执行，需要独立授权构建与新SHA，机器/会话准入和实际挂载哈希门 | 同上、DRAFT_GUARDS_REGRESSION.log、EXECUTION_READINESS.md |
| Q10 建议申请吗 | 可以申请严格限定这4运行的新授权；当前不建议直接启动。先补齐实时机器/会话准入，后续只按既定配对执行，不扩样本 | EXECUTION_READINESS.md |

明确状态：

- **CPU Go**：此前官方Linux单次135/135验收的冻结源码、证据与实际500.100秒边界复核通过；本轮新增本地3项Duration、3项保护测试通过。
- **Quota Go**：无需因“794秒”假象等待下次配额重置；那是SDK丢失天数，并非真实raw余额。
- **GPU Resource No-Go / 待机器与会话准入**：不声称当前硬件容量和账户并发已确认。此No-Go不是配额不足。
- **Experiment Authorization：NOT_GRANTED**。冻结草案不解除保护，无模型服务或GPU启动。
- **Algorithm Evidence：真实EarlyEGV NOT_RUN**。CPU scripted HTTP不能证明真实Gemma自主委派、提前正确修复或修复率收益。

正式提交没有重复发起；没有持续后台监控。此次保存Notebook状态查询遇到限流，未用猜测补全。
旧Prompt/ZIP/Trace/JUnit/CPU失败/STOP/协议/状态快照与原INTEGRITY_MANIFEST全部保留。
新的清单仅覆盖本目录，并显式排除自身及Python缓存。
''')
    emit('QUERY_AND_LIMITATIONS.md', '''# 查询范围与限制

query_kaggle.py执行了一次配额查询、一次提交列表、own保存Notebook完整分页以及每个返回ref的一次状态查询；随后只读取得旧GPU Smoke的保存版本metadata。
没有save_kernel/create_kernel_session/cancel_kernel_session/competitions submit调用。
GetAcceleratorQuotaStatistics的HTTP POST是只读RPC，不是资源申请。
所有请求设置30秒timeout；没有在限流后反复补查或启动后台轮询。

原始SDK字段使用camelCase；notebooks列表返回slug为空、ref有效。因此逐项status_*.json文件名碰撞成status_.json。
该单文件仅保留最后一次错误，不能用作完整会话审计；完整逐ref响应与时间均在notebook_statuses.json聚合记录中，没有丢失该聚合。
原执行脚本保持原样以便追溯；不建议直接重跑其全账户165次状态批次。后续准入应使用平台只读session管理或有限、顺序、遇429即停止的查询。
该执行失误与官方Agent/模型HTTP观察器无关，未修改任何研究执行器。

sdk_surface.json记录实际安装版本和可调用端点名称；SDK_KERNEL_PUSH_SOURCE.txt是本机已安装CLI的只读源码摘录（保存完整函数以核查参数），从未调用该写接口。
SDK_DURATION_SERIALIZER.txt为实际安装的序列化类源码；DURATION_REGRESSION.log证实days丢失及小数格式异常。

一般窗口资料：https://www.kaggle.com/docs/notebooks 、https://www.kaggle.com/docs/efficient-gpu-usage ，2026-10-20查询。
前者官方搜索索引显示CPU/GPU一般12小时；直接open两页均只返回标题、无正文。因此只作规划参考，不作为当前账户或NvidiaL4精确最大窗口证明。
未登录新的浏览器账号、未开启Notebook编辑器会话来尝试分配资源。
get_kernel旧版本的machineShape=NvidiaL4只证明保存配置，不证明即时库存；reserved=0不证明所有交互会话已结束。
后端推理日志和实时4L4硬件无法在本轮无GPU边界内实测，保持UNKNOWN/NOT_RUN。
''')
    print('Wrote additive reports; no frozen files changed.')
