# E1 分级预注册协议

本文件与机器协议 `experiments/e1-public-01/protocol.json` 配合使用。机器协议在官方 CPU 成功并取得任务快照哈希后、任何本轮 GPU 任务推理前保存和推送。历史协议、候选、原始输出都不修改。

## 固定任务与选择依据

只使用任务元数据及原始 Issue，不打开参考 Patch/test_patch 内容挑题。公开 Issue 自身的修复提示属于原始输入，不额外删改。公开题可能已有预训练污染，不能当隐藏榜泛化证明。

| 阶段 | 任务 | 类型 | 顺序 |
| --- | --- | --- | --- |
| Gate2 smoke | requests_7328 | 重定向 history 对象自引用及旧行为 | A/B |
| Gate3 screen_a | requests_7427 | no_proxy 域名边界语义 | A/B |
| Gate3 screen_a | rich_3894 | 非字符串 __qualname__ 接口兼容 | B/A |
| Gate3 screen_b | fastapi_14794 | Response 依赖注入与原生注入保持 | A/B |
| Gate3 screen_b | fastapi_14349 | JSON Schema 特殊键边界 | B/A |

A=control，B=e1_output8192。smoke 仅基础设施检查，**排除主效应分析**。正式筛选最多四题/八次，三仓库；官方129题只有四仓库，唯一HTTPX题已经暴露，因此不伪称取得四个新仓库。全部历史开发/正式配对题列入排除清单。每臂从同一不可变官方快照独立重建，禁止复用另一臂工作目录、Patch 或轨迹。

## 固定参数

31B QAT 模型 version2；完整权重、tokenizer、模板、config SHA 在机器协议中冻结。Wheelhouse 使用既有官方逐 Wheel 字节 SHA，本轮安装前再次核验；变动即停，不用相同版本号替代字节身份。

两臂 Agent300秒/计费工具60/单命令120秒；thinking4096；include_thoughts省略；seed17；官方默认采样。唯一因素输出cap16384/8192，thinking属于总输出，不重复预留。上下文32768、安全1024，最终消息+工具+模板经实际 vLLM tokenize；保留完整Issue，不靠丢需求准入。压缩 interval5/overlap1/threshold8192/retention4，两臂相同。所有摘要请求也使用本臂登记输出cap/思考/seed，纳入HTTP消费；这是研究执行器条件。

阶段上限：Agent准备180、Agent330（其中30为取消收尾宽限）、Patch60、Verifier准备180、应用60、验证300、落盘60、清理120、安全60，外层1350秒。既不将 Agent 扩大到330，也不使用冲突的12分钟外层。每批最多四次，最坏90分钟任务槽+45分钟启动+15分钟收尾=150分钟；smoke为105分钟。三批最坏6.75节点小时/27个L4 GPU小时，实际另报。不自动扩到8题，不运行 E2–E4 GPU。

## Gate1

原有38项官方Linux CPU/API、5项静态打包、新配置/边界测试、五个候选的完整 Compiler→空State Session→ADK Runner→模拟HTTP路径。另测include_thoughts false/true、thinking0/512、seed省略、工具回合reasoning历史及JSON一次编码。HTTP模拟不是Gemma推理。

只有同源码SHA的完整CPU门通过才构建GPU Notebook。冻结旧源码被 Windows checkout 改换行时，上传使用旧工作目录中与r12注册SHA一致的原始字节，不重写冻结文件；此过程记录在构建器。

## GPU 门与全局止损

先一个全新A/B smoke。每次必须有正确实际模型路由/参数、tokenizer与服务usage一致、工具调用、原生Trace、Patch检查点、真实官方Phase2、工作进程树停止与sandbox清理。最终还独立检查模型服务器进程树。无缺失才启动 screen_a；审计其完整输出通过后才启动 screen_b。

首个兼容、上下文、环境、泄漏、清理或证据失败停止整个系列。不临时改源码继续同批、不补跑凑分母、不更换任务/预算。正常断言失败且证据完整可继续。空Patch/无Phase2按unknown保留；收集错误先记unknown待独立环境归因，不凭exit2判模型修复失败。原始TaskResult字段保持不变，研究字段单独存在。未开始记录not_run。

## 分析

报告所有五个任务/十个槽位。四个筛选配对都完整且无unknown/not_run才报告主终点；否则主效应和完整率结论为null。报告 A-only/B-only/双方成功/双方失败以及净差，n4仅描述，不从一次随机胜出推断可靠提升。

次指标：非空及确认应用Patch、collection错误、HTTP与原生LLM计数、计费与原生工具事件数、完整HTTPusage（含压缩）、finish_reason length、Agent/worker耗时、首个编辑动作、测试与submit事件、重复读取。首个“有效”编辑和每次新证据需内容审查，不能用工具名、自述或token减少代替。没有可信测量时记null。未返回usage不能填0；官方total_tokens占位0保留并另报实际HTTP。

确认效应不使用smoke、历史formal-paired-01或CURE合成题。只有筛选支持修复方向且成本可接受才登记新的独立确认集。本协议不授权正式榜单提交或LoRA。
