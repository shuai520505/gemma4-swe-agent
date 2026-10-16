# Harness V2 开发运行及归因

这些结果用于验证基础设施，不构成V0/V1配对对照或排行榜成绩。Pilot 01保持原样，未补跑或拼接。

## 2.0.0 / infra-dev-01 / r07 / GPU Notebook v1

2026-10-15 23:18（UTC+8）完成。指定官方31B v2、4×L4，使用已通过31项官方Linux CPU测试的核心运行时。注册：`registrations/r07-gpu.json`。

| 预指定任务 | 实际状态 | 官方验证 | 调用与耗时 | 证据 |
| --- | --- | --- | --- | --- |
| requests_7315 / V0 | resolved | 原始resolved=true，exit=0，1 passed | 17次官方LLM调用、15次工具；官方264.408秒、控制器277.558秒 | 非空Patch 1534字节，在Phase 2前保存；完整边界Trace、增量事件和测试输出；进程停止、清理确认 |
| rich_3777 / V1 | unknown | 导入阶段ImportError，没有官方TaskResult、Patch或Phase 2 | 控制器4.009秒；官方调用计数缺失，不能写0 | worker_top_exception及stderr保留；进程停止，清理未确认；阻止继续接纳 |

基础设施门禁未通过。不得将这两道不同任务计算为V0/V1成功率，也不能将Notebook COMPLETE解释为两道任务完成。第一题是指定Gemma的真实官方单题通过记录；整批环境完整性不足，不能用于比较候选。

上下文探针：tokenizer和生成接口均为19输入token，指定模型返回2输出token。超限探针总预留37428（20020+16384+1024）在生成前被拒绝。第一题18次准入均在预算内，最大输入8389、最大总预留25797，全部输出预留均为16384，其中3次请求恢复原始Issue；官方LLM计数17与准入次数不完全相同，保留两个原始口径。探针单独使用8输出token，不改变任务Agent上限。

按单工作进程的monotonic时间线，原生事件中17次可取得usage的响应，与最近一次请求准入的输入token逐项完全一致，最大误差0，覆盖真实工具上下文；另1次准入没有对应的原生usage，不能单独声称已交叉验证。逐项数据及源成员哈希在 `docs/validation/harness-v2/gpu-r07-usage-crosscheck.json`。

### 跨题依赖污染的证据与边界

确认事实：两个沙箱的stderr均记录ensurepip失败并回退；第一题官方流程包含裸`pip install ... -e /workspace`，第二工作进程在导入google.auth.transport.requests时找不到requests。原始第一题Agent工具轨迹中没有pip安装命令。第一题退出时目录清理和进程树停止均为true，说明这些字段不足以证明共享Python包未被改变。

源码支持的机制：swegemma0.2.11的SubprocessManager.start()允许回退venv通过system site-packages导入pip，却不保证venv/bin中存在pip入口；exec()的PATH下一项为宿主Python目录。官方install_editable_package()使用裸pip，因此可能执行带宿主解释器shebang的入口，令editable安装指向随后被删除的工作目录。这是最符合现有证据的原因；旧运行未记录pip解析后的绝对路径或包删除前后快照，不能声称已从旧Trace直接观测到每个卸载动作。

2.0.1新增独立回归复现同一fallback条件，在可丢弃父venv中安装夹具版本，再让沙箱安装另一版本，核验父venv与下一沙箱未变；不对本机或Kaggle全局requests做破坏性卸载。pip和pytest入口均绑定沙箱Python，先核验sys.prefix；失败则禁止开始安装。它处理已知PATH/解释器缺口，不把本地subprocess沙箱称为操作系统级安全隔离。

### 原始文件

`artifacts/harness-v2/r07/gpu-output/files/harness_v2_gpu/20261015T150057_240641Z.zip`：169373字节，SHA-256 `37dc4ad905a01210bfe7d89bc74b689388facc48e807adc7440875f1b9b07aa1`。

ZIP CRC、全部24项注册源码及证据manifest均已核验。只读审计在 `results/r07-gpu-audit.json`，完整原生日志在同级 `gpu-output/native-kernel.log`。第二题原始failure_stage为null，事后从明确的worker_top_exception定位为worker bootstrap；原记录没有被回写。2.0.1提前记录prepare_agent/worker_bootstrap并修复该归因缺口。

## 2.0.1 / infra-dev-02

这是新的开发实验，重新执行CPU门禁；相同两道开发题仅用于验证环境链路。r08增加pip隔离；r09再将共享pytest启动脚本绑定沙箱Python，避免裸pytest使用宿主解释器读到错误包。每一修订保留独立注册、源码哈希和输出，不覆盖r07，也不把新旧记录拼成一个完整对照。当前实际门禁及后续执行结果见 `VALIDATION.md`。

### r10 / GPU Notebook v2 实测

| 任务 | 规范化状态 | 原始结果和证据 |
| --- | --- | --- |
| requests_7315 / V0 | resolved | 官方resolved=true，exit=0，1 passed；20次LLM、18次工具；官方145.555秒、控制器158.823秒；1447字节Patch先于Phase 2保存，原生Trace和清理均完整 |
| rich_3777 / V1 | unknown | 控制器734.082秒，在prepare_verifier的180秒阶段截止；观察到64次LLM、60次计费工具，计数标censored；没有官方最终结果、没有Phase 2退出码；进程树确认停止，目录清理未确认，禁止继续 |

第二题的完整原生Agent边界Trace和增量事件都已保留。Agent在413.479秒结束；读文件35次、运行命令25次，耗尽60次计费工具后edit_file返回BudgetExceeded，最终Patch为0字节。不能把空检查点称作有效Patch。原始审计中的native_trace=false仅对应未生成的最终harness/traces文件；不等于边界Trace丢失，独立ZIP审计已经确认边界Trace存在且冻结Prompt/模型匹配。

确认的Harness错误：观测子类使用DurableManager名称，而官方0.2.11的install_editable_package、install_test_dependencies和验证器使用type(manager).__name__判定subprocess。子类名称不匹配，使原本应跳过的Docker安装分支运行。日志中三次命令摘要可与 `python3 /tmp/setup.py --fast-path Textualize/rich` 的SHA-256逐字匹配：`84ab5e0b1334ebd40e7fee3ab9bd821379d64c7e412413655086587e5337679a`。Verifier准备中一次安装120秒退出124，随后再次执行同一安装，在阶段累计180秒时被父控制器终止。不能通过提高预算掩盖该分支错误，也不能将其写成Agent测试失败。

因此r07/r10均不能作为正式比较数据。此前对共享pip入口的风险推断仍成立，但更直接的诱因是观测子类改变了官方setup分支；2.0.1仅加固pip/pytest入口没有修复这一语义偏差。2.0.2恢复原生SubprocessManager类名约定，保留观测别名DurableManager，新增真实官方API回归确认两个setup函数均保持原生跳过行为。没有针对rich编写例外。

r10原始ZIP为339521字节，SHA-256 `b32ded44a848f31aa6692b70969e2c9f75ca4a2af4fcb560bc204f9e32c566e5`。CRC、全部28项注册源码和证据manifest通过，详见 `results/r10-gpu-audit.json`、`docs/validation/harness-v2/gpu-r10-dispatch-cause.json`。两题共91次请求准入，均在预算内，0计数错误或越界请求。

## 2.0.2 / infra-dev-03

r11是新的开发注册，保持同一模型、Prompt、六工具、阶段预算和两道预指定题。修复官方subprocess分支兼容性，并为审计显式区分空Patch字节数、Agent边界Trace和最终Trace；上下文错误单列context_admission阶段。先重新执行官方CPU/API门禁，未通过前不得启动GPU。


### r11 / GPU Notebook v3 实测与预算审计

| 任务 | 原始 Phase 2 | LLM / 工具 | 官方 / 控制器耗时 | Patch |
| --- | --- | --- | --- | --- |
| requests_7315 / V0 | resolved=false，exit=1，1 failed | 28 / 26 | 301.888 / 314.529 秒 | 1820 字节 |
| rich_3777 / V1 | resolved=true，exit=0，99 passed | 59 / 57 | 376.519 / 389.183 秒 | 1393 字节 |

requests 是真实断言失败：预期保留 `//v:h`，实际返回 `/v:h`；没有测试收集错误或环境异常。rich 的原生验证完成。两题均保存非空 Patch（先于 Phase 2）、完整原生边界及最终 Trace、增量事件、官方结果和验证输出；进程树停止、目录清理确认。未发生控制器超时。它们是不同开发题，不输出正式修复率或 V0/V1 优劣结论。

4 张 L4、31B v2 模型、六工具及冻结 Prompt 已核验。两题共 93 次请求准入，输出预留均为 16384、最大总预留 26414，0 越界、0 计数错误；87 个可取得原生 usage 的响应与 tokenizer 逐项完全一致（误差 0）。另 6 次压缩请求准入没有独立原生 usage，明确保留缺口。探针仍在生成前拦截 37428 总预留请求。

此前额外 Docker setup 命令的 SHA 在两题均为 0 次；4 次沙箱解释器准入均绑定各自 venv，第二工作进程正常导入。Verifier 准备约 1.094 / 1.337 秒，实际 pytest 命令约 1.164 / 2.179 秒。原始 ZIP 为 373874 字节，SHA-256 `ac494ea58ffd07483c4a5f44b7f0d5797d2d96f4c6c1d2e702e1a4770a742d81`；CRC、manifest、28 项源码及原始冻结证据均核验。只读结果见 `results/r11-gpu-audit.json`，逐事件/usage/命令核验见 `docs/validation/harness-v2/gpu-r11-forensics.json`。

**额外发现，不隐去门禁缺口：** r11 自动链路门禁为 true，但人工预算审计发现官方内嵌 Python Patch 应用脚本没有匹配到原先只识别裸 git/patch 的阶段检测，应用时间记入 prepare_verifier。这不改变已完成的原生测试结果，但独立 apply_patch=60 秒截止尚未覆盖该官方路径，因此不能据自动 true 放行正式对照。

## 2.0.3 / infra-dev-04

r12 保持模型、候选、工具、两道开发题和预算不变，仅识别官方内嵌应用脚本的固定 Usage 协议，进入 apply_patch 阶段后恢复先前阶段。新增真实官方 helper 回归检查调用时阶段为 apply_patch；不按任务、答案或 Patch 内容分支。先以 AST 加载的原生 helper 重放证实旧识别器停留 prepare_verifier，再修正并通过重放；初次本机重放缺少 PYTHONPATH 的启动失败日志也保留，不冒充有效红测试。完整官方 API 回归须在新 Linux CPU 门禁中执行。原 r11 注册、日志和结果全部保留。


### r12 / GPU Notebook v4 最终实测

2026-10-16 15:08:29（UTC+8）采集到 COMPLETE；实际运行 ID `20261016T064721_516615Z`。

| 任务 | 原始 Phase 2 | LLM / 工具 | 官方 / 控制器耗时 | Patch |
| --- | --- | --- | --- | --- |
| requests_7315 / V0 | resolved=false，exit=1，1 failed | 20 / 18 | 245.725 / 258.457 秒 | 1654 字节 |
| rich_3777 / V1 | resolved=false，exit=1，96 failed、3 passed | 53 / 53 | 489.593 / 502.417 秒 | 689 字节 |

requests 的断言仍是应保留 `//v:h` 而返回 `/v:h`。rich 达到官方 8 分钟 Agent 截止（阶段观测 480.004 秒），自动回收未提交修改并继续验证；其 Patch 使 Console 初始化对只读 is_interactive 属性赋值，真实测试产生 AttributeError。最终分类 failed 的依据是已经完成的官方验证，不是将超时占位值当失败；原始 error_message 仍保留 Agent exceeded session timeout。不能因它超时就丢弃随后实际取得的测试证据。

**人工基础设施准入通过。** 两题均有完整官方结果、非空 Patch（验证前已保存）、原生边界及最终 Trace、增量事件和 Phase 2 输出；清理确认、进程树停止，没有控制器截止。两题各 2 次官方 Patch 应用（Agent Patch 与验证 Patch）均实际进入 apply_patch，累计观测约 0.104 / 0.104 秒，回到准备阶段后继续执行。真实 pytest 命令约 1.171 / 5.842 秒；阶段区间约 1.191 / 5.872 秒。旧 Docker setup 命令均未出现，4 次沙箱解释器前缀及入口绑定通过。

80 次请求准入全部在预算内，最大总预留 27219，Agent 输出预留始终 16384，0 越界、0 计数错误。73 个原生 usage 响应与 tokenizer 完全一致，最大误差 0；7 次额外压缩准入无独立 usage，保留缺口。超限探针 37428 总预留在生成前拒绝。指定 31B v2、冻结候选 Prompt、4×L4 和官方包版本均匹配。

原始 ZIP：437375 字节，SHA-256 `fe3cc96d0d97abcba6f938da340ec482f5d3c3fc6b2eb486b00b4f39308b5e25`。CRC、manifest、28 项注册源码和原始冻结证据均通过；只读审计 `results/r12-gpu-audit.json`；原始 Phase 2、控制器结果、阶段和 usage 对应关系索引在 `docs/validation/harness-v2/gpu-r12-*`。完整 Trace/Patch 保留于本机/private Kaggle 原始 ZIP。

结论：允许进入**另行预注册**的正式配对实验；本阶段不执行正式八次对照。Harness 的可靠性门禁通过不代表候选解题能力通过。上一修订 rich 曾为 resolved，本轮失败，不能选取较好的一轮拼接、不能把不同开发题当 V0/V1 对比，也不能将这两题外推为榜单成绩。

### 当前提交与拿分判断

2026-10-16 使用已授权 CLI 只读查询 `kaggle competitions submissions -c gemma-4-developer-agent -v`，返回 `No submissions found`，尚无官方分数。冻结 V0/V1 ZIP 的 CRC 和根目录 agent.yaml 结构通过，官方 CPU 编译测试已覆盖两候选；技术上可以作为首次探分输入。比赛实际提交是 Agent 配置 ZIP，官方隐藏任务通过率才产生分数；本机开发结果不能上传替代分数，也不能保证正分或高分。

Harness V2 不打包进 Agent submission。冻结 ZIP 仍声明 60 分钟 / 100 工具 / 单命令 300 秒，开发实验明确覆盖为 8 分钟 / 60 工具 / 单命令 120 秒；官方评分行为不能直接等同于本轮。建议先依新协议完成配对比较、确认最终提交预算，再选择一个独立版本探分；需要修改候选预算时创建新候选，保留原 V0/V1。用户本次询问提交可行性，没有执行排行榜提交。

官方依据：[竞赛评估说明](https://www.kaggle.com/competitions/gemma-4-developer-agent/overview)。官方评分按验证通过比例；总 Agent 运行上限 12 小时（含准备，不含 Patch 验证）。该上限不能用本地批次 1530 秒外层配置替代。
