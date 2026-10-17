# 官方 CPU / Runner 验证

真实 Kaggle Linux、官方 Wheelhouse 安装；不是本机替代包或Gemma推理。

| 修订 | Notebook保存版本 | 真实结果 | 后续 |
| --- | --- | --- | --- |
| r01 | gemma4-s1-e1-01-r01-cpu v1 | 61项，51通过，10失败，0error/skip | GPU禁止；原ZIP与失败日志保留 |
| r02 | gemma4-s1-e1-01-r02-cpu v1 | **63/63通过，0失败/error/skip** | 相同源码允许构建最小GPU smoke |

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
