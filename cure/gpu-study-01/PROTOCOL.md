# CURE GPU Mechanism 01：执行前冻结协议

实验单位为同一合成场景的一对独立运行，实验ID `cure-gpu-mechanism-01`。基于7aa7801；研究核心0.1.0及cpu-r03的59项源码不变。全部机器可读任务、初始代码快照、Issue/base/SHA、候选成员哈希、Wheelhouse逐文件SHA和执行顺序见 [protocol.json](protocol.json)。协议SHA256：`5a4c237f3ec7c5f7dd9927769b283831a024317192f47efe8bf9a5144c8bbbb5`。

## 固定配置

官方 `google/gemma-4/Other/gemma-4-31b-it-qat-w4a16-ct/2`，4×L4，单Agent，六个原生工具。两臂300秒/60工具，单命令120秒；max_output_tokens8192、thinking_budget4096、include_thoughts=true、seed17、temperature0.2、top_p0.95、top_k40。上下文32768、安全量1024；r12原有准入/压缩/持久化保持一致。每次完整外层1350秒。每个GPU Notebook预留45分钟安装启动与15分钟落盘，最多四次任务，预算150分钟以内。

B ZIP：`f002c3c5cba1f629f2cce7608d2d72ac389af8a3ee03760257e1aff011844798`；C ZIP：`01e2a6271cab07356b7696cc21d82d9011ce88869a4a2bd4df68c62138a7634c`。不修改候选Prompt。模型revision在运行前固定；首次生成前对模型全部文件（包括权重、tokenizer/template）记录SHA manifest，后续Notebook必须匹配首对manifest。Wheelhouse必须逐字节匹配既有实际清单，漂移即停止，不能自动升级。

## 场景与顺序

| 槽位 | 场景 | 顺序 | Notebook |
| --- | --- | --- | --- |
| 1–2 | lumen：新增入口、保留旧入口和调用方输出；迁移文档的“无调用方”假设可被实际客户端否定 | B / C | smoke |
| 3–4 | harbor：构造时绑定默认依赖，保留显式且falsey的注入对象 | C / B | followup_a |
| 5–6 | cedar：None/0/负数边界及源列表保持 | B / C | followup_b |
| 7–8 | orion：新增缺省行为，保留0、负数、转换与异常 | C / B | followup_b |

首对必须完整通过兼容性与证据门后，才可运行followup_a；其通过后才可运行followup_b。首次基础设施或证据门失败即**全局停止**。不更换任务，不重试运行，不按结果改参数，不用旧实验或挑选重跑补齐。官方库内部既有请求重试策略保持原样，实际HTTP尝试全部记录；它不等于允许重新启动实验槽位。

## 数据分离

GPU源码bundle不含 `scenarios.py`、参考替换串、脚本修复器、CPU场景decoder或evaluation-references.json。每个Agent快照仅含初始仓库、公开测试和Issue；Task.patch为空。独立隐藏测试由官方Task.test_patch进入**新的Phase 2 sandbox**。参考修复仅用于本地/CPU验证评估器并单独保存，不传给模型。原生subprocess隔离不是恶意代码安全边界；审计实际HTTP输入和工具命令，核查是否出现评估测试或越出仓库读取答案。任何泄漏使机制结果不可用。

## 门禁与判定

运行前：冻结源码与cpu-r03门匹配，原有63项再通过；新场景本机基线红/参考绿；在官方CPU运行时确认四个参考Patch均通过真正Phase 2。参考修复成功不算模型能力。

首对：核查真实vLLM路由、最终HTTP生成参数、/tokenize与响应prompt_tokens逐请求一致、原Issue保留、reasoning历史实际字段、边界请求在发送前拒绝、原生Trace、Agent边界Trace、Patch检查点、官方Phase2执行和进程树/沙盒清理。确认的断言失败允许作为机制负结果；收集/环境错误、未知结果或证据缺失停止后续。

机制主观察：两臂是否发现相同契约；是否有**可定位的先前主张被真实工具结果否定**，以及在继续原编辑前是否出现相关的inspect/probe/有依据修改。仅文档中的错误假设不自动成为模型的错误假设；若模型从未采纳它，则“反证改向”机会缺失，记不可评估，不能计成功。C的decision_changed及JSON只作自报，以两臂原生工具调用和结果为判断依据。

逐事件记录定位、调用方调查、复现、编辑、回归、提交，以及重复/无效动作；保留模糊判定。分析者可见轨迹和结果，无独立盲审，属于机制探索而非因果效应估计。B也可能主动反思，不能将顺序Prompt当作模型绝不改向的保证。

报告官方resolved原值、Patch、真正Phase2、HTTP实际LLM调用/token、工具调用、Agent与完整任务时间。缺失结果写unknown，未启动写not_run。工具重复统计须考虑前后工作树变化，不能把修复后的重跑当无效重复。四个合成场景不计算Kaggle正式Resolution Rate，不推断榜单提升。无LoRA、S0变更或正式提交。
