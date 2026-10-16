# Harness V2：预算准入、进程隔离与持久证据

基线提交 `6b8a0ba`；初始Harness版本 `2.0.0` / `harness-v2-infra-dev-01`，随后为 `2.0.1` / `harness-v2-infra-dev-02`；进一步确认观测子类改变官方setup分支后新增 `2.0.2` / `harness-v2-infra-dev-03`。所有尝试使用独立 revision 和运行目录，不能合并成 Pilot 01 的补跑结果。V0/V1 的6个源文件、两个候选ZIP，以及 Pilot 01 协议/记录/原始输出保持冻结。

本阶段只修改本地实验基础设施。`harness_v2/` 不进入 Agent submission；仍使用指定官方 Gemma 4 31B v2、六个工具、单Agent。没有 Prompt 优化、LoRA 或多Agent。

## 已确认的约束来源

| 项目 | 实际来源及证据 | V2处理 |
| --- | --- | --- |
| 32,768 上下文 | 官方 Getting Started 的 `VllmConfig(max_model_len=32768)`；Pilot 01 的 `vllm_config.json` 与 vLLM 0.19.1 日志确认实际生效 | 保持32,768，不能解释为该模型在所有环境下的能力上限 |
| 16,384 输出预留 | 校验过SHA-256的 `swegemma==0.2.11` wheel，`config.py::build_submission_limits()` 的 `GenerationConstraints.defaults` | 保持Agent默认值。官方允许范围1..32,768，但本轮不搜索采样/输出上限 |
| 请求参数 | `google-adk==1.36.1` 的 `lite_llm._get_completion_inputs()` 将 `max_output_tokens` 映射为 `max_completion_tokens`；LiteLLM交给本地OpenAI兼容服务 | 在LiteLlm公开的 `llm_client` 注入只负责准入的客户端，观察最终序列化messages/tools/模板参数，不修改官方包文件 |
| 历史压缩 | 官方ADK `EventsCompactionConfig`；触发依据包含最近一次prompt usage，存在滞后；不是一次请求的完整容量证明 | 提前到8,192 token阈值，保留4个原始事件，interval5/overlap1；两候选相同 |
| 压缩请求 | 官方 `LlmEventSummarizer` 构造的LlmRequest没有显式输出上限 | 对缺少上限的请求显式应用官方16,384默认值；不能让压缩调用绕过预算检查 |
| 原始版本 | Pilot 01实际为vLLM0.19.1、LiteLLM1.82.4、Torch2.10.0+cu128、Transformers5.13.1 | 使用官方离线wheelhouse及其原样安装方式，记录运行实际版本；不把旧本地requirements当成Kaggle实测版本 |

源码来自 `scripts/official_wheels.json` 中5个已校验wheel，解包副本位于本地 `artifacts/harness-v2/official-source/`。参见[官方说明](https://www.kaggle.com/code/ryanholbrook/getting-started-gemma-4-developer-agent)、[官方比赛规则](https://www.kaggle.com/competitions/gemma-4-developer-agent/rules)和[vLLM 0.19.1 tokenize协议](https://github.com/vllm-project/vllm/blob/v0.19.1/vllm/entrypoints/serve/tokenize/protocol.py)。这些是本地实验的受控配置，不声称修改了官方排行榜评分Harness。

## P0-A：每次请求的上下文准入

`context_budget.py` 使用正在服务该模型的 vLLM `/tokenize`，传入同一份messages、tools及chat_template_kwargs，包含特殊格式/生成起始标记。只接受服务返回的32768容量，核算：

`实际输入token + 请求输出预留 + 1024安全余量 <= 32768`。

默认输出16384时，允许输入上限为15360；15361被明确拒绝。tokenizer不可用、计数缺失、容量不符或超限都在生成请求发送前抛出可归因异常，并持久化decision/counts；不使用字符数估计替代真实tokenizer，不忽略错误继续发送。正式GPU准入还需要最小GPU smoke确认真实tokenizer路径。

原始Issue正文作为独立不可改写的核心内容保留；若ADK压缩后的user消息已不包含它，重新插入逐字相同的正文再计数。Issue本身太大则报告unknown，不删核心要求。冻结的系统Prompt源码不变。恢复正文会增加token，计数包含这部分开销。

通过官方 `HarnessLimits` 将run_command返回上限设为2000字符、read_file为120行/4000字符。截断仍由官方工具执行并返回原有截断信息；不修改六个工具的实现、名称或参数。该处理可能影响定位能力，属于后续两组共同的Harness变量，不能混入Prompt改进效果。

ADK摘要仍可能遗漏历史细节；恢复Issue不能证明其他历史全部保真。超限时的明确拒绝防止无效请求，但不等于任务修复成功，也不保证所有轨迹都能继续。

## P0-B：阶段预算及批次容量

| 阶段 | 上限（秒） | 说明 |
| --- | ---: | --- |
| Sandbox A准备 | 180 | 创建、快照、离线依赖和基线；不占官方Agent 8分钟 |
| Agent推理及工具 | 510 | 官方Agent仍480秒；控制器另留30秒退出余量，单命令120秒，60计费工具 |
| Patch保存 | 60 | 原生fallback/显式提交、Agent边界Trace |
| Sandbox B准备 | 180 | 独立基线和验证依赖 |
| Patch应用 | 60 | Agent Patch、保护文件处理及验证Patch |
| Phase 2测试命令 | 300 | 保持官方验证超时 |
| 结果落盘 | 60 | 原生结果、Trace和审计输出 |
| Sandbox清理 | 120 | 两个沙箱的清理，独立于Agent计时 |
| 外层安全余量 | 60 | 启动/阶段切换/调度 |
| **整题外层** | **1530（25.5分钟）** | 包含所有阶段；不再使用12分钟外层 |

Pilot 01 的Agent超时实际约483秒，进入B后又等待约236秒就遭旧外层截止，无法确认当时卡在准备还是测试。上述预算覆盖480+300秒及准备/清理余量；它是基于观测的初始配置，不是性能保证或卡住必能恢复的证明。父进程同时执行阶段与整题截止。

正式8次对照草案拆成2个独立Notebook，每批4次，严格按两个完整任务配对切分，不拆开同一题的V0/V1。每批 `4×25.5 + 45启动 + 15收尾 = 162分钟 < 180分钟`。共同模型启动单列；接纳下一题前检查是否还有完整slot及收尾余量。任何重试都用新ID并保留首次失败。

## P0-C：证据路径与取消边界

旧 `evaluate_with_deadline()` 只对同一Python进程里的async任务取消；`asyncio.to_thread` 的底层同步工作可能继续。旧最终Trace导出还依赖 `evaluate_task()` 返回。V2保留旧文件作为基线，另用 `supervisor.py` 为每题启动独立工作进程。

Linux使用独立进程组；Windows CPU回归使用Job Object，在挂起状态分配后恢复进程，包含后代并在关闭时终止。工作进程拥有自己的sandbox_tmp和日志目录；vLLM由Notebook父进程持有，模型服务不在被终止的任务进程组内。父进程监督阶段、外层截止和后代存活状态，异常后阻止下一题，并停止本批共享模型服务。

2.0.0的真实GPU开发运行显示，进程/目录清理不能证明宿主Python依赖未变：ensurepip失败的官方venv回退路径可能把裸pip命令解析到宿主入口。2.0.1在每个官方沙箱创建后、安装前核验sys.prefix并写入只位于该venv/bin内的pip及pytest启动脚本，统一通过沙箱Python的`-m`调用，记录sandbox_python_admission。没有修改工具或官方wheel；共享只读包仍可继承，不能宣称操作系统级隔离。安全回归在可丢弃父venv内验证版本替换与下一沙箱导入，细节和证据边界见 `harness_v2/RESULTS.md`。

2.0.1的第二次GPU进一步确认，官方0.2.11通过type(manager).__name__区分subprocess和Docker。原观测子类名称DurableManager误入了Docker editable安装和依赖安装分支，导致额外setup命令及准备截止。2.0.2使用继承原生管理器的SubprocessManager类，并保留DurableManager导入别名，恢复官方字面类名约定。真实官方API回归要求两个setup函数保持原生直接返回，且管理器仍为原生类型的实例；不改官方wheel或针对某仓库跳过流程。这同时恢复验证器的原生JUnit报告检查分支。该兼容点依赖已锁定的官方版本，升级前必须重跑API回归。

持久化位置如下：

- `events.jsonl`：阶段、活动、命令哈希/类型/退出码、预算准入和计数，逐条flush+fsync；同阶段的进度更新不重置截止。
- `adk_events.jsonl`：经官方 `SwegemmaContext.handle_adk_event()` 公开方法收到的事件JSON，去重追加。
- `incremental_trace_legacy.json`：收到事件的持续镜像，原子替换；明确标注不是完整官方原生Trace。
- `patches/<sha256>.patch`：显式提交、原生git diff、Agent返回边界和finally可取得的Patch，内容寻址且不覆盖旧版本；`latest.patch`仅为最新检查点。
- `agent_boundary_trace*.json`：原生Agent返回后、调用Phase 2前立即保存的完整Trace与Patch；不再等整个验证返回。
- `phase2_execution.json` / `phase2.log`：官方沙箱测试命令返回后、验证沙箱清理前保存的退出码和输出。
- `official_result.json`：官方TaskResult的JSON字段原样导出，Trace对象另存；不追加伪造的官方字段。
- `official_harness.log`及原生 `harness/logs/`：持续原生日志，quiet显示模式确保文件日志接收事件。
- `audit_result.json`：独立的规范化分类、控制器错误、清理确认和证据完整性标志。

公开Evaluator配置没有暴露内部SessionTrace实时回调的注入点；V2不修改官方包内部全局对象。事件镜像因此可能缺少系统/任务prompt、某些compaction自定义事件；完整原生Trace在Agent边界返回后取得。若硬截止发生在此之前，只报告增量镜像和真实信息缺口，不宣称已保存完整Trace。正在编辑但尚未提交/提取的工作树也可能没有可用Patch；没有数据不能填造。

结果/进度文件使用临时文件+fsync+原子替换；Patch版本和日志使用追加/独占创建。每次输出目录独立，ZIP拒绝覆盖。进程树停止和沙箱目录清理是两个不同字段：强制停止后即使进程已无存活，也不能假装正常清理完成或继续接纳任务。

## P0-D：结果分类

| 规范化状态 | 需要的证据 |
| --- | --- |
| resolved | 官方最终结果明确resolved=true |
| failed | 有官方完成的非零测试结果/收集错误或明确Agent Patch应用拒绝；保留具体阶段 |
| unknown | 官方结果缺失、上下文/API/环境错误、Agent/Verifier/外层超时；不能填成官方失败 |
| not_run | 计划中未接纳或因本批中止尚未执行 |

先前Agent超时不能抹去随后实际完成的验证断言失败；Verifier超时则没有完整功能判定。所有官方原始值保留，规范化字段单独记录。控制器错误/清理异常不改写已有官方resolved，另标controller_failure_stage并禁止继续。

只在预定数据齐全且没有unknown/not_run时提供完整成功率。观测均值必须给出样本数与截断情况，不把缺失计数记成0；开发smoke不输出版本优劣或修复率结论。新正式实验见 `harness_v2/FORMAL_EXPERIMENT_DRAFT.md`，通过基础设施门禁后另行注册。

2.0.2额外明确patch_checkpoint_bytes，0字节不等于有效修改；agent_boundary_trace与最终native_trace分别标记。硬截止前已有完整Agent边界Trace时，不因最终TaskResult尚未生成而误报全部Trace丢失。上下文计数/越界异常归入context_admission阶段，仍保留先前错误之后实际完成的测试判定优先级。

## 验证门禁和版本历史（当前结论见 VALIDATION.md）

初版26项本地CPU回归已通过，覆盖输入15360/15361、核心Issue保留、计数服务失效、压缩输出默认值、Agent/Verifier/外层超时、已有Patch无最终结果、父进程提前退出、清理延迟、配对拆批、完整比较分母和原始哈希不变。脚本化结果明确标注CPU fixture，不是Gemma修复。

官方Linux API/工具链CPU门禁另在私有Kaggle Notebook执行。r04因错误的LiteLLM开发版本要求在安装阶段失败；r05因启用依赖解析而碰到官方wheelhouse不含的可选依赖失败，均未执行模型推理。r06采用官方Notebook原样的离线全量wheel安装（--no-index --no-deps --force-reinstall）重新验证。所有失败输出保留；门禁不允许把安装失败当成测试通过。

官方CPU r07 / Notebook v4已经31项全通过、0跳过；r06暴露的编译器复制客户端问题已通过保留单任务内guard/journal绑定解决，并经真实编译器回归确认。GPU开发smoke按新注册配置执行，正式GPU对照仍禁止。最终真实状态以 `harness_v2/VALIDATION.md` 为准；必须具备官方CPU通过日志、最小GPU基础设施结果和冻结候选核验，才可讨论正式实验。

r07真实GPU探针及第一题Phase 2完成，第二题在导入阶段失败，整批门禁未通过。2.0.1重新走CPU→GPU流程；禁止以旧CPU通过记录为已改动的核心运行时放行。后续生成器也补齐官方INSTALL/SERVER失败分支所需的ZIP别名，并经注入异常的本机测试验证。

r10已通过35项官方CPU检查并执行GPU，但第二题因上述观测子类错误在Verifier准备截止，完整边界Trace得以保留。2.0.2/r11重新执行本版本官方CPU门禁，随后才可再做开发GPU验证；最终准入结论以 `harness_v2/VALIDATION.md` 为准，不能将前一修订的通过自动传给新核心源码。


2.0.3 / infra-dev-04（r12）：r11 已取得两题真实 Phase 2 及完整清理，但人工审计发现内嵌 Python 的官方 Patch 应用脚本未进入独立阶段。观察器补识别官方 `apply_patch.py` Usage 协议，应用时使用既定 60 秒阶段预算，完成后恢复准备阶段累计时间；原生 helper/API 回归验证，不改官方脚本或候选。正式准入仍待本版本 CPU→GPU 开发门禁。
