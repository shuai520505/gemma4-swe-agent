# 历史 13 次编辑失败审查
证据来自已验证的六次实验原始归档；只读分析，未重新运行 Gemma，未修改 SDK 或工具实现。完整逐次证据见 EDIT_ERROR_EVIDENCE.json。
13/13 的服务端 HTTP `tool_calls` 均只有 `filepath`、`new_string`，缺 `old_string`；13/13 的 `new_string` 含有字面量 `old_string`。HTTP→ADK 参数逐值相同，未观察到该边界的参数变换；13 次均因必需参数检查而在生产编辑执行前被拒绝。工具 schema 已明确声明三个必需参数。
每次错误都进入后续 HTTP 请求。前 12 次的反馈请求有 HTTP 200 响应，支持反馈进入后续模型交互；第 13 次只有携带反馈的发出记录，随后超时取消，不能保证服务器已接收。
13 次只有两种完整参数值：11 次为先前参数的完全重复；最后一次改变了参数内容，仍缺同一参数。按缺参结构计算，首次之后有 12 次同类无效重试。不能写成模型从未调整，也不能把内容调整当作有效恢复。
| 次序 | HTTP→ADK | 明确错误反馈 | 近端分类 | 原始生成/Parser 起因 |
|---|---|---|---|---|
| 1 | 参数一致 | 后续 HTTP 200 | TOOL_SCHEMA_REJECTION | UNKNOWN |
| 2 | 参数一致 | 后续 HTTP 200 | TOOL_SCHEMA_REJECTION | UNKNOWN |
| 3 | 参数一致 | 后续 HTTP 200 | TOOL_SCHEMA_REJECTION | UNKNOWN |
| 4 | 参数一致 | 后续 HTTP 200 | TOOL_SCHEMA_REJECTION | UNKNOWN |
| 5 | 参数一致 | 后续 HTTP 200 | TOOL_SCHEMA_REJECTION | UNKNOWN |
| 6 | 参数一致 | 后续 HTTP 200 | TOOL_SCHEMA_REJECTION | UNKNOWN |
| 7 | 参数一致 | 后续 HTTP 200 | TOOL_SCHEMA_REJECTION | UNKNOWN |
| 8 | 参数一致 | 后续 HTTP 200 | TOOL_SCHEMA_REJECTION | UNKNOWN |
| 9 | 参数一致 | 后续 HTTP 200 | TOOL_SCHEMA_REJECTION | UNKNOWN |
| 10 | 参数一致 | 后续 HTTP 200 | TOOL_SCHEMA_REJECTION | UNKNOWN |
| 11 | 参数一致 | 后续 HTTP 200 | TOOL_SCHEMA_REJECTION | UNKNOWN |
| 12 | 参数一致 | 后续 HTTP 200 | TOOL_SCHEMA_REJECTION | UNKNOWN |
| 13 | 参数一致 | 请求已发出，接收 UNKNOWN | TOOL_SCHEMA_REJECTION | UNKNOWN |

模型解析前的原始 completion/token 文本未保存；HTTP JSON 已经过服务端工具解析，因此 13 次的 MODEL_GENERATED_MISSING_ARGUMENT 与 PARSER_DROPPED_ARGUMENT 都保持 UNKNOWN。ADK_ARGUMENT_TRANSFORMATION 在已见边界没有证据；根因不能从最终报错直接倒推。
R1 直接覆盖已确认的完整参数、错误反馈处理与禁止等价重试现象，但“主要错误来源是模型还是 Parser”仍未知。仅靠 Prompt 的解决概率没有数据可估；它值得独立初筛，不能承诺收益。若 Parser 对合法原文存在解析错误，Prompt 不保证解决。
潜在 Gemma4 Parser/SDK 兼容性需要单独保留为待调查项：未来在明确授权的研究运行中增加解析前后只读证据，再做离线解析对照；本轮不改官方工具、不重跑模型、不靠兼容补丁遮盖失败。
归档 SHA256：`328dda4a3084f306f7fec75e7e207b4a5f26292dea9ba3853f9e6a57e73396c6`；wire、ADK、native trace 文件哈希见配套 JSON。原始内容和模型推理轨迹保留私有，只发布结构、计数和关联证据。
