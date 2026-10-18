# E1 GPU Smoke 02：真实启动通过，配对停止，四题筛选 No-Go

**未获得完整 A/B 配对，不能判断 8192 是否提高修复率。** 新实验
`s1-e1-outputcap-smoke-02` 的真实 GPU 启动门通过。A 执行到 300 秒截止，
保存了可应用 Patch，并完成真正的官方 Phase 2；一条请求缺少响应/取消终态，
触发预注册证据门。B 未启动，记为 `not_run`，没有补跑或拼接。
Phase 2 同时暴露 194 个 fixture setup errors，因此 A 的研究归因为
`unknown`，不能把原生 `resolved=false` 直接归因于修复算法。

本轮没有正式 Kaggle 提交。唯一已确认榜单成绩仍为 S0 Public 0.13，
Submission 57261002。本 Smoke 不进入后续四题主效应估计。

## 注册、版本与完整性

- 远程核对起点：`be8c80efc65866f31fdaf6e9f0a4455347cb3b99`。
- GPU 前已推送的预注册提交：`dd5dfbca7332a309d4edd558e1f8fd19d8951fc8`。
- 协议 SHA-256：`6a30e7220d7bd04bc9d428c8c877705a44d2360f1cac7c08a276fa675b5d22c0`。
- GPU Notebook SHA：`9828acb54e16f5dcc4ac1c93f044383b7fb327467e613d691a6466fe6002ed5b`。
- 官方 Linux CPU：**77/77，通过且零跳过/错误/失败**，包括完整重跑的 r04 71 项。
- r04 原 80 个注册文件逐字节不变；独立启动观察器等五个文件形成 85 文件上传。
  CPU/GPU 源码一致，模型八文件、Wheelhouse 逐文件和任务哈希均验证一致。
- 执行前后 945 项原始基线、8 个历史 CURE 原始包、501 项已有 S1 文件哈希均未改变。
  S0、V0/V1、CURE、r12、E1 候选及旧 STOP 均未修改。

模型固定官方 Gemma 4 31B QAT version 2，实际路由为
`/kaggle/input/models/google/gemma-4/other/gemma-4-31b-it-qat-w4a16-ct/2`，
4×L4、TP4、32768 context、bf16、Gemma4 tool/reasoning parsers，未启用 LoRA。
详细文件哈希见 [protocol.json](protocol.json) 和 [registration.json](registration.json)。

两候选仍为冻结的原 S0 Prompt（SHA
`5f43c3a546c4c21765aff5e09a92126b1bb104b6e8423b269364a0b8f286a7ce`）。
A ZIP：`8835fd8ab4bdd43f5fcf74423c8ed2c3b9e0e0711686c8eac335b22c1da9da12`；
B ZIP：`61d0084f666b2e0911792f286cf5ef25d023241262385061d4ad172eed75a590`。
只有输出上限 16384/8192 不同。300 秒 Agent、60 工具、120 秒命令、thinking4096、
seed17；`include_thoughts` 与 sampling 默认项继续省略。Thinking 包含在输出上限内。

任务为 `requests_7328`，base `cbce031327be4f1b4b5fd041ff4dcaa8efa2ce53`，
Issue SHA `88117c4cfe2520e07fb29dfc35d2653e60a334b9a058072ea9df62ac79dd216c`，
快照 SHA `47f35331fd2dc1d976eeb2aeff5f8aa376cd005911bf35ce164161931a97d8c9`。
工具轨迹未发现请求参考答案或隐藏测试的调用。B 未启动，不能声称两臂隔离已实测通过；
A 的 Agent 与 Verifier 使用两个独立 sandbox，均清理完毕。

## 真实启动门

私有 [GPU Notebook](https://www.kaggle.com/code/wudangdexiaodoashi/gemma4-s1-e1-smoke02-smoke)
保存版本 1，平台状态 COMPLETE。实验状态为 **STOPPED**，两者含义不同。

实际执行原 r04 `s1.preflight.check_model`，包含显式 `tools=None`。
`/health`、`/models` 成功，模型与注册路径一致；真实模型生成一次 `READY`，
usage 为输入 16、输出 2、合计 18，与 tokenizer 完全相符。
第二次真实 tokenizer 计得输入 30019，加 16384 输出预留及 1024 余量共 47427，
保护器拒绝发送该超界生成请求。启动门耗时 4.728 秒，单独计量。
完整请求/响应、tokenizer 输入/结果和准入事件位于
[startup/startup.jsonl](results/gpu/startup/startup.jsonl)。

Notebook 全局时钟从 setup 开始。首次服务启动准入时已计入安装/哈希的 777.168 秒；
A 前已计入 1081.298 秒，仍余 9718.702 秒，1350 秒完整任务槽与 900 秒收尾预留均通过。
没有模型启动后重置时钟。全部 25 条任务请求准入通过；24 条已收到响应的模型路径、
输出/Thinking/seed/sampling 语义及 tokenizer/usage 一致。第 25 条只观察到请求。

## A/B 对照表

Token 数只包含收到的 **24 个响应**，不是完整的 25 请求总成本。
最后请求 tokenizer 输入为 7453，但其服务 usage 和生成 Token 无记录，不能补成零。

| 指标 | A：16384 | B：8192 | B−A |
|---|---:|---|---|
| Agent 真实启动 | 是 | 未启动 | 不可计算 |
| HTTP 请求 / 响应 | 25 / 24 | 未运行 | 不可计算 |
| 官方 LLM 调用计数 | 22 | 未运行 | 不可计算 |
| 已收响应 Input Tokens | 123109，部分成本 | 未运行 | 不可计算 |
| 已收响应 Output Tokens | 9662，部分成本 | 未运行 | 不可计算 |
| 已收响应 Total Tokens | 132771，部分成本 | 未运行 | 不可计算 |
| Agent 时间 | 299.998 秒，触发 300 秒截止 | 未运行 | 不可计算 |
| Worker 总时间 | 392.770 秒 | 未运行 | 不可计算 |
| 工具调用尝试 / 官方计数 | 23 / 22 | 未运行 | 不可计算 |
| 首次有效文件写入 | 151.102 秒，复现脚本 | 未运行 | 不可计算 |
| 首次生产代码有效编辑 | 258.497 秒 | 未运行 | 不可计算 |
| Patch 可应用 | 是，5244 字节、3 文件 | 无 Patch | 不可计算 |
| 修复正确性 | 无法由本次环境确认 | 未运行 | 不可计算 |
| 真正 Phase 2 | 完成，74.294 秒，exit 1 | 未运行 | 不可计算 |
| 官方 raw resolved | false | 无官方结果 | 不可计算 |
| 研究归因 | unknown：环境/证据阻断 | not_run | 无成功率估计 |
| 正常 submit_patch | 0，超时后原生 fallback 保存 | 未运行 | 不可计算 |
| 上下文 / 截断 | 0 拒绝；24 响应无 length；末请求未知 | 未运行 | 不可计算 |

22 个已完成 Agent 响应与两次 compaction 响应形成 24 个已收 HTTP 响应；
另有一条未终结请求，因此不能把官方 LLM 计数或占位 `total_tokens=0` 当作总开销。
全部 25 次实际发送的 tokenizer 输入累计 130562，这与已收服务 usage 的口径不同。
原始推理历史和工具消息保存在 `http_wire.jsonl`；逐请求摘要见
[control-requests.json](analysis/final/control-requests.json)，包含最后的缺失响应行。

## A 的逐事件审计

时间从官方 Agent 会话开始计量；有效编辑取成功返回时刻，不能把调用名当作成功。
完整 23 次调用参数与返回值见 [工具事件 JSON](analysis/final/control-tools.json) /
[CSV](analysis/final/control-tools.csv)。

| 事件 | 秒 | 实际行动与结果 |
|---|---:|---|
| 1–6 | 4.938–36.601 | grep/send/resolve_redirects 定位，四次读取 sessions.py，有区间重叠 |
| 7–8 | 128.220 | write_file 漏必填 filepath；随后运行不存在的脚本失败，均不算有效编辑 |
| 9 | 151.102 | 成功创建 repro_self_ref.py，首次有效写入；后续原生 Patch 也保留该文件 |
| 10 | 177.244 | 脚本 AttributeError，PreparedRequest.headers 未初始化；堆栈来自系统安装的 Requests |
| 11–17 | 182.684–222.438 | 继续查 sessions/models；一次 grep 无匹配退出 1；没有确认运行中的包来自编辑仓库 |
| 18–19 | 244.148–245.572 | 写入并运行硬编码列表操作的复现脚本，打印 Self-reference detected |
| 20 | 258.497 | 成功将 `hist[1:]` 改为 `hist[:-1]`，返回非空 diff，首次生产代码编辑 |
| 21 | 259.809 | 再跑同一硬编码脚本，仍打印 self-reference；没有执行修改后的实现 |
| 22–23 | 284.291–286.680 | 新建检查脚本后运行退出 0，但输出 History length: 0，未验证多跳中间响应契约 |
| 最后模型请求 | 286.742 | 准入后实际发送，截止前无已记录响应或取消终态 |
| 原生截止 / Patch | 299.998 / 300.034 | Agent 超时；原生 fallback 抓取 5244 字节 Patch，未显式提交 |
| Verifier | 301.198 起 | 两次原生 apply 路径均 exit 0，实际 pytest 执行并返回结果 |

总计 10 run_command、8 read_file、4 write_file、1 edit_file 尝试。官方工具计数为 22；
轨迹另含一次参数校验失败的调用。完全相同参数的 read_file 重复数为 0，但确有重叠读取。
五次 Python 检查包括不存在文件、初始化错误、两次相同的手写列表模拟，以及末次弱检查。
首个失败脚本堆栈明确指向 `/usr/local/lib/python3.12/dist-packages/requests/sessions.py`；
后续检查也没有显式证明导入编辑后的源码。这是验证证据不足，不能把其 exit 0 计作修复通过。

最终 Patch 修改生产文件并携带两个复现脚本。工具创建的 `test_redirect_history.py`
没有出现在原生 fallback Patch 中，与原生测试路径保护机制相符；未单独捕获过滤前的完整 diff。
唯一落盘 Patch 检查点 SHA 为
`a8a9b3ef7b276db797f0741ff48f109524b59d68793dd970c6557a45cb31de47`。
成功修改保存在截止后的原生提取点，不能声称存在每次编辑后的独立 diff 快照。

另外，`hist[:-1]` 排除了当前响应，但会保留原始响应；源码注释明确要求该循环忽略原始请求。
因此存在旧行为改变风险。这来自实际 diff 与原注释的静态比较，未使用参考答案；
本轮环境不能给它提供独立的官方正确性判定。

## 停止原因与归因边界

**证据门：** r04 `wire.py` 在发送前记录请求，在正常读取返回后记录响应，没有在
异常/取消路径记录终态。最终请求位于 286.742 秒，官方 300 秒超时，之后没有对应响应。
该时间线与取消导致记录缺口一致；没有显式取消事件，不能宣称已直接证明传输的终态。
缺口应归于研究观察器对取消覆盖不足，不是输出 cap=16384 导致失败的证据。
冻结门确实停止了 B，没有在同 ID 修补 gate 或补跑。

**Verifier 环境：** 真正的 Phase 2 返回
`142 passed, 1 skipped, 1 xfailed, 194 errors`，其中 190 个是 httpbin fixture
递归依赖，4 个是 httpbin_secure 递归依赖，没有 `FAILED` 断言条目。
原生 `resolved=false / test_exit_code=1` 与 r04 的 `failed` 规范化结果均完整保留。
新的离线研究归因单独写为 `unknown / verifier_environment`。
底层原因可能是 fixture provider 未安装、未加载或路径/插件配置不一致；本轮没有作
依赖清单/加载状态探针，不能把其中某一个猜测写成已验证原因。

**清理：** Worker exit 0，进程树确认停止，Agent 与 Verifier 两个 sandbox 都有 stop
事件，目录无残留。服务树观察到 7 个 PID，剩余 0，未使用强制清理。
本次不存在下一任务并发污染证据；B 根本未启动。

## Q1–Q5 与后续决定

1. **8192 是否减少上下文预留压力？** 数学上输入准入从 15360 增至 23552，
   多 8192 tokens。A 实际最大输入 10899，最小安全余量 4461，未遇准入压力。
   B 未运行，没有实测的上下文改善数据。
2. **是否改变工具、编辑或验证行为？** 无完整对照，不能回答。A 的晚编辑、复现
   开销与弱验证是观测事实，不能归因于输出 cap 或推断 B 会改善。
3. **是否发生截断/推理损失？** 24 个已收响应均未 length，最大 completion 3230，
   小于两种 cap；末次请求未知，B 未运行。既不能声称 B 无损，也不能声称 cap 导致超时。
4. **双方是否完成有效 Patch 和 Phase 2？** A 有可应用 Patch 和真实 Phase 2，
   修复正确性未确认；B 无任何任务结果。因此不是完整配对。
5. **是否进入 E1 四题筛选？** **No-Go。** 先在新的基础设施版本和 CPU 研究中
   验证取消终态记录、明确 partial usage、区分 fixture setup 错误，并在不使用参考修复的
   任务 sandbox 检查中验证包导入路径及官方基线 fixture 环境。然后另行预注册新首对。
   不改冻结 Prompt，不把本次 A 与未来 B 拼接，也不自动启动任何新 GPU 批次。

最小后续工程修正是让观察器对 CancelledError/异常记录请求 ID 与终态，并把预计截止的
取消和意外证据丢失分开；未取得的 usage 仍须保留 unknown。必须先加 CPU 取消回归，
不能事后放宽本次门。同时需查明官方任务 fixture 环境，而不是修改 Agent 来迎合测试。

## 真实成本与档案

Notebook 日志覆盖 1503.578 秒，约 **25.06 分钟**，含安装、哈希、加载、A、Verifier
和导出。服务启动前全局耗时 777.168 秒，A 前 1081.298 秒。A Agent 299.998 秒，
Verifier 执行 74.294 秒；B 没有 Agent 开销。启动探针另计 4.728 秒/18 tokens。
按已确认的四设备乘日志时长，约 **1.671 L4·小时占用代理**，不是 Kaggle 精确计费值，
也不是纯推理 GPU 利用时间；未把排队或三小时预留算入此数。

原始 GPU ZIP：`results/gpu/raw.zip`，753773 字节，SHA-256
`6f7ce7cec7979921e8cfae11e3f80411f6398281f1c5a2e461b42a5a57b03128`。
CRC 和 152 个清单条目通过；嵌套 A 原始 ZIP 的 27 个清单条目也通过，SHA
`15f4db26788e720e8719a7311b46bbd207a75f5bd1536e145d8d047b11e1a3a3`。
完整源载荷、安装日志和原生证据在该 ZIP 中；便利副本均来自相同字节。
原生 Trace/Patch/Phase 2 都保留，**完整性缺口是最后一个模型请求的响应/取消终态**，
不能因为 ZIP 哈希通过就声称所有语义证据完整。

参见 [STOP.json](STOP.json)、[最终研究比较](analysis/final/comparison.json)、
[完整性审计](analysis/final/integrity.json)、[运行前后原证据核验](post_execution_integrity.json)。
原始结果与后续归因分开，任何未来实验都需要新 ID；本次没有修复率、榜单提分或金牌结论。
