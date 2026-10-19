# s1-egv-mechanism-smoke-01 — frozen before GPU

2026-10-19 Asia/Shanghai。用户本轮明确授权一个配对，基础提交e355ce1。
CPU03原生环境及115项兼容回归全部通过后冻结；在任何GPU启动前推送GitHub。
所有后续结果在独立目录追加，协议、Prompt、ZIP和已冻结源码不得热修或重跑。

## 身份与执行

固定fastapi_15800，顺序EGV→Control，沿用先前草案选择，不按本次结果替换。
base f1d750fddad90e2faad6c3cc5c85c7687b787e89；Issue SHA
85c676765d59e203b9e78c89f06dd4fbf7ed3e469ec298892f08fd3ae12e4a11；
快照39db9ef995f8066b5f3cc70a7d8c54325e7bdc4faa9599e76099b533a4e034c0。
全任务记录及Evaluator测试补丁的opaque SHA在selection.json及protocol.json固定；
未读取参考修复。CPU基线结果和评估测试只在Evaluator侧，不交给Agent。

EGV ZIP cefadd019ec64d9d06cbde72e0d0507796e8af9a370dd2358059e211845135e9。
Control ZIP 8835fd8ab4bdd43f5fcf74423c8ed2c3b9e0e0711686c8eac335b22c1da9da12。
完整Prompt/member哈希、精确103词diff哈希、模型8文件、41个模型wheel及124个任务wheel、
154个执行文件逐一SHA、实际CPU版本和原生基线原始结果SHA全部在protocol.json中。
两臂的YAML/config一致，仅Prompt不同；单Agent、原生六工具，不含其他候选因素。

Gemma4 31B QATv2，4L4/TP4，context32768/safety1024，output16384，thinking4096，
seed17，Agent300秒，60工具，单命令120秒。include_thoughts/采样参数继续省略。
原生Verifier300秒，worker外层1350秒，服务器空闲观察最多60秒。
10800秒全局窗口从Notebook设置开始计，预留900秒落盘/清理；模型启动前须有
1200秒启动+两臂完整槽位，首臂前也须同时准入两臂。不是实际消耗报告。

CPU环境再次在GPU宿主模型启动前准入并核验实际依赖版本。固定模型/源码/wheel哈希，
health/models/tokenize，真实READY生成、tokenizer/usage一致、超界拒绝、三次连续
running=waiting=0才进入首臂。READY是独立16输出且关闭thinking的原有启动探针，
不是Agent生成参数；成本单列。两臂均从独立干净Agent、工作区、Patch和Verifier开始。
只用原生Phase2结论，不替换测试、依赖、fixture、断言或评分规则。

## 冻结链

- protocol.json SHA b117f403548e874dcc2928e92d53b853101ec5eaf3b8e8669ff7059b83dc379b
- CPU03 raw SHA 12aebe6825033a8be451d9f40f54fecb5f6f2bcb3daf89ca3af1afa98d601c11
- GPU Notebook SHA 269470a6de7b01dee63e2a2433838ba97e370a4aac9345669145ff103b76f2a7

gpu_notebook.json固定完整执行载荷SHA和protocol SHA；freeze_manifest.json同时绑定
协议、Notebook、元数据、执行注册、候选及CPU原始包，避免自引用哈希。此整套文件
在同一GPU前Git提交中封存，之后才能dispatch。新协调器与冻结E3入口的全部差异
见coordinator.diff：候选路径/顺序、FastAPI观测前缀、CPU门、版本检查、READY精确检查
和完整剩余配对时间准入。冻结worker/guard/工具/HTTP/Verifier实现没有改动。

## 终点、审计与停止

主终点为完整官方resolved，保留test_exit_code/TaskResult及原始Phase2。unknown和
not_run不算确认失败。原生JUnit在清理前复制，要求XML/统计/退出码/终态一致。
普通调用失败、合法resolved=false、已解释Agent截止和fallback Patch可以继续另一臂。
setup/collection不自动等于环境：须结合基线、改动字节和实际调用链；无法归因则停止。

每个HTTP request_id应有真实response/cancel/timeout/transport_error终态，CancelledError
继续传播；未收到usage保留null，合计标partial。客户端取消不证明后端终止：两臂间
要求3次间隔至少1秒的服务器零running/waiting快照，不能伪造逐请求abort确认。
Trace、工具参数/返回、Patch与源码版本、工作区导入/sys.path、原生JUnit/stdout/stderr、
worker/sandbox及服务器清理持续保存。漂移、污染、泄漏、不明HTTP终态、JUnit冲突、
环境归因不明、清理/idle失败、时间不足或关键证据损坏触发全局STOP；未启动臂not_run。
禁止同一冻结批次重跑、修复后续跑、换题或拼接旧轨迹。

先隐藏候选标签、最终成败及模型自述，逐个审查可独立判断的工具动作，封存第一轮判断
后揭盲。研究员已经读协议，故不是独立双盲。审计必须覆盖：

- validity：输入是否达到目标；无效命令/无效输入/纯打印弱探针分别标注。
- provenance：真实当前工作区模块/源码SHA；仅导入不等于目标函数执行。
- novelty：代码、输入、环境或可检验假设是否改变；不能仅凭重复次数判浪费。
- consequence：反证后是否有实际修改或合理停止；不是模型自述遵从就有效。

有效assertion、弱显示探针、无区分力重复、合理修复后回归、旧行为覆盖、反证修订、
诊断残留、稳定编辑与显式提交/fallback分别记录。少工具/早编辑不能替代正确性。
实际响应Token与未观测usage分开，启动及CPU成本分开；GPU占用只报告可核实代理。

EGV独赢或同成功且更省成本/覆盖未降，只支持另一次独立确认。双方失败但动作改善
最多是机制线索，不自动扩大；正确性/旧行为变差或没有有意义行为收益且成本更高，
No-Go并暂停Prompt-only EGV。单题配对不能估计总体修复率或金牌/前五概率。
不运行第二组任务、LoRA、其他因素或正式Kaggle提交；S0已记录唯一正式分数仍0.13。
