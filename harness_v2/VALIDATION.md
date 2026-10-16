# Harness V2真实验证记录

本文件只记录执行过的检查及当前门禁；CPU脚本化结果不是Gemma修复成功。新正式配对实验未执行，未进行排行榜提交。

## 已执行

| 环境 / 修订 | 真实结果 | 解释 |
| --- | --- | --- |
| 本机Windows / 控制器r07 | 26 tests，全部通过 | 含上下文15360/15361、计数失败、Issue保留、各阶段/外层超时、孤儿进程、清理延迟、Patch检查点、结果分母和配对拆批 |
| 原始V0与Pilot 01保护 | 原始V0 39项哈希及V2冻结清单76项均匹配 | 原Prompt、候选ZIP、Pilot 01原始记录/Trace/协议保持不变 |
| Kaggle CPU / r04 / Notebook v1 | 安装失败，未执行测试 | 错误要求本地开发版LiteLLM1.83.14，官方wheelhouse实际运行版1.82.4 |
| Kaggle CPU / r05 / Notebook v2 | 安装失败，未执行测试 | 依赖解析要求wheelhouse未提供的可选包；不能把安装阶段当测试通过 |
| Kaggle CPU / r06 / Notebook v3 | 27 tests，26通过、1失败、0错误、0跳过 | 官方API、真实六工具及Linux超时控制已运行；编译器复制客户端，守卫绑定身份测试失败，阻止GPU |
| Kaggle CPU / r07 / Notebook v4 | **31 tests全部通过，0失败、0错误、0跳过** | 修复GuardedClient任务内复制生命周期，新增批次与完整分母检查；完整官方API与Linux工具/控制器门禁通过 |
| 本机 / Notebook生成器异常分支 | 2 tests通过 | 注入真实安装命令异常和启动接纳异常，检查诊断ZIP及原始异常；不调用模型 |
| GPU / r07 / Notebook v1 | 第一题resolved，第二题unknown，整批门禁未通过 | 真实31B及tokenizer探针通过；第二工作进程导入requests失败，不能以Notebook COMPLETE宣称任务全部完成 |
| Kaggle CPU / r08 / Notebook v5 | 35 tests，34通过、1失败、0错误、0跳过 | 新隔离夹具使用宿主/tmp wheel路径，被官方路径翻译改写，未进入安装检查；失败ZIP与日志保留 |
| r09 | 未执行 | 准备了pip及pytest入口的注册输入，修正夹具路径前未启动Notebook；不能列为测试结果 |
| 本机 / 2.0.1控制器 | 27 tests全部通过；隔离单元2项通过 | 新增工作进程导入失败阶段归因及解释器前缀检查，不代表GPU门禁通过 |

CPU使用官方curated wheelhouse原样离线安装：`--no-index --no-deps --force-reinstall`。r06实际核心版本为swegemma0.2.11、adk-submission0.2.13、adk-eval-core0.1.0、google-adk1.36.1、google-genai2.11.0、LiteLLM1.82.4。没有运行CPU版Gemma推理。

官方CPU Notebook：[gemma4-harness-v2-cpu-validation](https://www.kaggle.com/code/wudangdexiaodoashi/gemma4-harness-v2-cpu-validation)。每次结果保存在本地不同revision目录，不能将后续通过覆盖前次失败。

## 可核验的超时证据

本地 `artifacts/harness-v2/cpu-worker-evidence-07/` 保存真实启动的脚本化工作进程输出：

- `test_agent_stage_deadline_retains_evidence/`：Agent阶段截止，已有Patch保留，官方最终结果不存在，分类unknown。
- `test_verifier_stage_deadline_retains_patch_and_native_trace/`：验证阶段截止，Patch及事件检查点保留，分类unknown。
- `test_patch_survives_outer_timeout_without_official_result/`：外层截止，整棵进程树终止；不生成假的official_result。
- `test_cleanup_delay_blocks_next_run_without_erasing_native_result/`：官方结果样例已为true，但清理超时；原值仍为true，控制器单列cleanup异常并阻止下一题。
- `test_launcher_exit_does_not_kill_still_running_worker/` 和 `test_orphaned_worker_is_stopped_at_outer_deadline/`：分别验证启动器提前退出与孤儿子进程停止。

这些CPU夹具不调用模型，不参与任务成功率。Kaggle r06同类Linux测试通过；原生API测试确认ADK事件在任务返回前落盘，且原生Agent边界Patch/Trace在最终结果生成前可读取。增量镜像不能冒充完整原生Trace，信息缺口见设计文档。

Kaggle r07 CPU ZIP内7项真实进程夹具的逐项状态、Patch哈希和原始成员哈希另保存在 `docs/validation/harness-v2/cpu-r07-timeout-evidence.json`；超时项均为unknown且禁止接纳下一题。`harness_v2/audit.py` 从ZIP只读核验注册源码、原始证据和候选模型/Prompt，审计结果与原生结果分离。

GPU v1提交后，代码复核发现生成器复用官方INSTALL/SERVER诊断分支时缺少 `bundle_run` 别名。先以注入安装失败的测试复现NameError，再补绑定并验证安装/启动两条异常路径。红/绿日志全部保存，第一份绿日志中的Notebook路径/哈希来自拦截写入的测试构建，并未重写r07的真实Notebook。修正只用于后续新构建；正在执行的r07注册Notebook、CPU验证过的核心运行时和候选保持不变，不声称这条新异常路径已通过GPU执行验证。

## GPU及正式实验门禁

当前：**不允许正式GPU对照实验**。2.0.0 / r07 GPU已实际执行且整批基础设施门禁未通过，真实结果和归因见 `RESULTS.md`、`results/r07-gpu-audit.json`。2.0.1 / 新实验ID `harness-v2-infra-dev-02` 重新执行官方CPU门禁，在其通过前不得用r07旧CPU结果放行新GPU。不能直接续接Pilot 01剩余五次。

最终结论必须同时考虑真实CPU门禁、GPUtokenizer/路由探针、开发任务结果、清理和证据完整性；模型任务失败与基础设施错误分别报告。正式实验仍需另行注册。

## 数据集操作记录

首次CLI上传误用了公开参数，产生只含新控制器和候选配置的临时公开输入；没有上传Pilot原始证据、参考答案或凭据。Kaggle拒绝公开转私有后，已删除该临时数据集。新建 `wudangdexiaodoashi/gemma4-harness-v2-private-input` 已通过服务端metadata核验 `isPrivate=true`。r01—r03只准备输入，未执行模型实验。

## 保存路径

本机日志、CPU原始ZIP、原生日志和安装记录位于 `artifacts/harness-v2/` 的各修订目录；精简可公开验证记录在 `docs/validation/harness-v2/`。注册配置在 `harness_v2/registrations/`，源码和编译/预算/事件接口设计见根目录 `HARNESS_V2_DESIGN.md`。
