# CURE GPU Mechanism 02 / C1：独立首对预注册

基线提交55e31b8，实验ID `cure-gpu-mechanism-02-c1`。[协议JSON](protocol.json) SHA256为 `c47ef237d0b95089ee117cee75c8b0c836270bcb93d350fc2c34bdb32a28864c`。原 `cure-gpu-mechanism-01` 保持停止状态，不覆盖它的候选、协议、结果或证据。

## 候选与范围

仅派生新C1；[精确Diff](candidate-exact.diff) 只有字面标记 `<cure>{JSON}</cure>` → `<cure>JSON object</cure>`。JSON状态示例和其余算法指令完全保留，agent.yaml、sampling.yaml、eval_config.yaml不变；内部Agent名也不更改。新ZIP只含原有四个配置/Prompt文件，研究控制器/测试/参考答案不进入提交包。[新旧成员SHA](candidate-derivation.json) 逐项登记。

旧C ZIP为 `01e2a6271cab07356b7696cc21d82d9011ce88869a4a2bd4df68c62138a7634c`；新C1为 `c1001800838f1465c1a6414685db239fb03f9a69b45bba6ff34c6232a6f2e612`。B继续使用冻结的 `f002c3c5cba1f629f2cce7608d2d72ac389af8a3ee03760257e1aff011844798`，不修改S0。

## CPU完整Runner门

使用官方ADK Runner、InMemorySessionService空state、官方编译器和六个原生工具；模型响应仅在httpx传输层模拟，counter也明确为CPU模拟。B与C1必须通过真实指令预处理并发出首次请求；冻结C必须以JSON变量KeyError在HTTP前失败。另检验双花括号负例、完整Prompt扫描及一处兼容差异。

成功请求要求最终system instruction包含完整原Prompt正文，并对C1 JSON示例做逐字节包含检查及json.loads验证；模型、8192输出、4096 thinking、seed17和六工具保持一致。旧C失败是预期回归，不能跳过；Runner.close实际执行。原63项API、预算、上下文、早期Patch、异常/清理回归一起重跑。CPU成功不是Gemma推理。

CPU首个push的title/slug规范化使账号实际Notebook ID为 `wudangdexiaodoashi/gemma4-cure-c1-mechanism-02-cpu`，CLI已明确返回该地址；原构建metadata和注册文件保留，实际执行ID另由collection记录。它不改变协议、候选或代码。GPU Notebook标题在创建前改为匹配已登记ID，避免再次歧义。

## 首对、固定参数与停止

仅运行lumen_interface_01的一对，顺序 **B一次 → C1一次**。base为 `47a1332014916c840c63a4d1980084f08e1481d9`，每次从相同冻结tgz建立全新Agent sandbox及新Verifier sandbox，沿用上次Issue和隐藏测试字节。**已经见过该场景的B行为，因此本轮是探索性兼容/机制验证，不是独立泛化证据。** 不复用上次B轨迹或Patch。

固定官方31B QAT模型版本2、全部模型文件SHA（来自已实测的原manifest，启动前逐项核对）、Wheelhouse逐文件SHA、4×L4。两臂300秒Agent/60工具、命令120秒，8192输出/4096 thinking、include_thoughts=true、seed17、temperature0.2、top_p0.95、top_k40；上下文32768/安全量1024及原压缩设置相同。每次完整外层1350秒，不改变核心worker、r12或工具。新session适配器仅加入完整CPU门和模型字节核对、替换候选目录，Diff见 [session-adapter.diff](session-adapter.diff)。

必须先通过63+5项CPU测试，并将匹配当前源码及注册SHA的CPU门放入GPU bundle，才构建/启动GPU。每次运行检查实际请求/响应/tokenizer、Trace、Patch、Phase2、进程树和sandbox清理。首个兼容/基础设施/证据门失败即全局停止，不临时修Prompt或控制器，不重试、不替换、不拼接。完成的断言失败属于真实结果，未知验证结论仍unknown。只允许这一对，不自动扩展余下三类场景、公开任务、训练或榜单提交。

模型只收到初始Issue/仓库/合法工具；隐藏test_patch由评估器保留到新Phase2。GPU bundle不含本轮参考修复、上次B工具轨迹或成功Patch。原63项CPU门的旧测试源码保留在研究侧作哈希校验，不作为模型答案。原生subprocess并非绝对安全边界，必须审计实际工具路径和HTTP输入是否泄漏评估材料。

## 三项独立判定

- A兼容性：CPU完整Runner发出正确请求，真实C1启动及请求/工具轨迹无模板错误。
- B机制：从原生工具序列及模型可见声明判断契约维护/更新、调查/验证行动、是否先有错误假设后被真实反证推翻。仅自报decision_changed或输出JSON不够；没有先前错误假设则改向机会缺失，不计成功。完整原Prompt进入请求证明可见，不自动证明遵从。
- C修复收益：记录两臂Patch、官方Phase2、调用/token/时间及C1增量；一个已暴露合成配对不能支持成功率或Kaggle分数提升。保留失败和模糊判定。
