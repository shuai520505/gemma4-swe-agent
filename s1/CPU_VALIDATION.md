# 官方 CPU / Runner 验证

真实 Kaggle Linux、官方 Wheelhouse 安装；不是本机替代包或Gemma推理。

| 修订 | Notebook保存版本 | 真实结果 | 后续 |
| --- | --- | --- | --- |
| r01 | gemma4-s1-e1-01-r01-cpu v1 | 61项，51通过，10失败，0error/skip | GPU禁止；原ZIP与失败日志保留 |
| r02 | gemma4-s1-e1-01-r02-cpu v1 | **63/63通过，0失败/error/skip** | 相同源码允许构建最小GPU smoke |
| r03 | gemma4-s1-e1-01-r03-cpu v1 | **66/66通过，0失败/error/skip** | 仅修复后的CPU门；原GPU实验已停止，不能继续 |
| r04 | gemma4-s1-e1-01-r04-cpu v1 | **71/71通过，0失败/error/skip** | 加入Notebook全局时钟门；没有新GPU运行 |

r01失败均为同一测试比较：计数前assistant工具消息保留content:null，LiteLLM实际HTTP省略该空字段。修正测试仅去除该确切字段后比较所有其余内容，没有放宽工具JSON、reasoning、Issue或生成参数的断言，也没有改变研究运行时。真实tokenizer是否等价由GPU逐请求usage核验，不以CPU模拟断言替代。r02另增加两项真实worker配置构建测试。

r02构成：原有38项Harness/API（含Agent、Verifier、外层超时、取消、Patch先落盘、清理和分类）；5项原静态/打包；8项新配置/边界；10项完整Runner；2项新worker实际EvalConfig/编译/Patch/清理构建。Worker测试用CPU fixture结果，明确没有真实推理/Phase2；真实工具执行仍由原API集覆盖。

完整Runner均经过官方Compiler、空Session State、完整候选Prompt指令预处理、工具调用和第二轮HTTP请求。测试捕获输入、system全文、六工具schema、reasoning历史、工具返回单次JSON编码、输出上限、thinking与seed。模拟HTTP和模拟计数器只证明配置/兼容性。

实际HTTP核验：

- 16384/8192分别成为max_completion_tokens；无人为temperature/top_p/top_k。
- thinking4096/512发送enable_thinking=true和对应thinking_token_budget。
- thinking0发送enable_thinking=false，不发送thinking_token_budget。
- include_thoughts=false且thinking4096仍开启生成，但第二轮剥离reasoning/reasoning_content。
- include_thoughts省略/true保留模拟返回的reasoning历史。thinking0测试仍故意返回模拟reasoning，用于验证桥接格式；不能据此声称真实关闭thinking后仍会生成思考。
- seed17发送17，省略seed不发送seed。
- 8192输出的输入临界值23552，16384输出临界值15360，均含1024安全量；多1token拒绝，计数错误关闭发送，Issue完整恢复。

包与版本：swegemma0.2.11、adk-submission0.2.13、adk-eval-core0.1.0、google-adk1.36.1、google-genai2.11.0、LiteLLM1.82.4。全部官方Wheel字节在安装前核验，见各raw ZIP/wheel_hashes.json。r02原ZIP SHA `d1ca7adc24bc0fa4185788816caba79260f1e69cefd71c09ede93c3008b3b3ba`；r01为 `22aba55fc4a6b2c72e3bd0aab8e4d45c475935cda16dc033710cc972e75795a4`。CRC和所有237/180个manifest条目分别通过核验。

门禁与完整日志、最终system、两轮请求保存在results/cpu-r02；raw.zip保留完整测试时源码。r01原始失败证据位于results/cpu-r01。GPU构建器只读取成功门及匹配源码SHA，不接受r01。

## GPU失败后的r03兼容修订

r02 GPU在首次生成探针漏传LiteLLMClient必需的tools参数，任务尚未接纳。完整ADK Runner会自动传这个参数，因此原63项检查没有覆盖**直接客户端启动探针**，不能据63通过推断该路径也通过。失败原样保存，实验s1-e1-public-01永久停止，本轮没有第二次GPU。

r03从session提取同一个preflight.check_model供实际启动与CPU回归共同调用，显式tools=None。新增三项：真实官方客户端复现旧缺参TypeError；同一探针函数经真实客户端→模拟HTTP，且超限请求不发送；已停止协议无法生成新GPU Notebook。源码发现同时排除_local/results/revisions，登记78项文件，没有r02的40个冗余CPU源副本。不是Prompt或生成参数调优；五个候选ZIP及Prompt SHA不变。

r03为38旧API+5静态+23新增=66。原始ZIP333184字节，SHA `68c8a7bb7d041005b9515d424a1e9d0a7bb2945cfe4527a541b4ec459f9d60b6`，CRC与207项manifest通过。证据见results/cpu-r03与revisions/r03精确diff。这里只证明API调用修正及CPU门通过；**没有真实Gemma生成或Phase2复核**。

## r04全局预算门

审计发现r02/r03 session内开启时钟没有覆盖此前安装及模型哈希。r04在Notebook首个setup单元建立SESSION_STARTED，显式必填传入session.run，SessionWindow以此统一核算启动、完整任务槽和900秒收尾。每次准入写入host journal；不改变两臂Agent300秒/工具60等参数。

新增五项测试：完整槽临界值及多1秒；安装/哈希耗时不能在server启动时重置；启动1200秒加完整任务槽预留；无效时钟/槽拒绝；实际session API必须提供Notebook起点。最终38旧API+5静态+28新增=71/71，耗时31.152秒（仅测试执行，不含安装）。CPU raw.zip352998字节，SHA `49e1124c94fa8977cd6c97b9c80bd0be5ff7dcfd190d42cc7092053917b15241`，213项manifest/CRC通过。

r04注册80项源码/配置，全部以本轮官方CPU输入验证。报告、收集器输出等非执行资料不改变候选。原r02协议和所有raw ZIP保持原样，r03/r04都是GPU停止后的CPU修订，绝不回填原GPU实验为通过。
