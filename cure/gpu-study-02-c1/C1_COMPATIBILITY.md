# C1兼容性修正与完整Runner CPU结果

本记录只针对CPU兼容阶段；真实GPU结论另见本轮对照报告，不能由此推导Gemma能力。

## 精确修正

仅将说明句 `<cure>{JSON}</cure>` 改为 `<cure>JSON object</cure>`。没有改真正的JSON示例、状态字段、行动选择、反证规则、成本估计、模型/工具、预算或生成设置。内部Agent名保持不变，新目录和新ZIP用于区分候选；旧C/B/S0完全不动。[精确Diff](candidate-exact.diff)、[逐文件SHA](candidate-derivation.json)。

| 字节标识 | 冻结C | 新C1 |
| --- | --- | --- |
| Prompt SHA256 | 300f1f1861ab00d1ada1af56a391afd800ad8d96858dd386e85e9b403e00df97 | 7a4b6547f139d7fbd466d891651ff3b75148cc5eba83854683624d2d581d058e |
| ZIP SHA256 | 01e2a6271cab07356b7696cc21d82d9011ce88869a4a2bd4df68c62138a7634c | c1001800838f1465c1a6414685db239fb03f9a69b45bba6ff34c6232a6f2e612 |

完整Prompt按官方ADK相同的花括号正则扫描，再用实际 `_is_valid_state_name` 分类：B无Session变量模式；旧C只有字面 `{JSON}` 被识别为变量；C1没有会被识别为变量/Artifact的字面标记。完整JSON对象里的带引号字段不被解释为合法状态名。[全量扫描](results/cpu/runner-evidence/complete-prompt-pattern-scan.json) 保留所有匹配，而不是仅grep已知错误词。

## 实际官方CPU运行

账号实际Notebook `wudangdexiaodoashi/gemma4-cure-c1-mechanism-02-cpu`，保存版本1，COMPLETE。[原有63项日志](results/cpu/original63.log)、[新5项日志](results/cpu/runner.log) 均通过，无跳过。CPU档案SHA256为 `f8079beec2e47f51ee36f3444899da2b84dcbf2c40d80d4ea34b5ce67ed455c3`。

测试真正执行 `compile_submission → google.adk.runners.Runner.run_async → instruction预处理 → LiteLLM → httpx.AsyncClient.send`；Session由官方InMemorySessionService创建，初始state为空。没有直接绕过Runner构造LlmRequest，也没有绕过模板报错。HTTP响应与token counter明确为模拟，不运行Gemma/vLLM。

| 完整Runner输入 | HTTP请求 | 实际结果 |
| --- | --- | --- |
| B完整Prompt | 1 | 正常，最终system包含完整原Prompt |
| 冻结C完整Prompt | 0 | 预期KeyError：Context variable not found: JSON |
| C1完整Prompt | 1 | 正常，完整Prompt与真正JSON示例原文保留，示例可json.loads |
| 旧C的双花括号负例 | 0 | 同一预期JSON KeyError；不是有效转义 |

第五项测试同时检查精确单处变化、三个YAML字节相同、完整花括号扫描。成功请求还检查六工具、8192输出/4096 thinking/seed17；每个Runner执行close。原63项继续覆盖预算、上下文边界、参数漂移、Patch检查点、异常与清理。

具体证据：[B渲染结果](results/cpu/runner-evidence/checklist/rendered-system.txt)、[C1渲染结果](results/cpu/runner-evidence/cure_v01_c1/rendered-system.txt)、[旧C失败](results/cpu/runner-evidence/cure_v01/result.json)、[双花括号失败](results/cpu/runner-evidence/cure_v01-double-braces/result.json)。[完整CPU门](results/cpu/full_runner_cpu_gate.json) 绑定注册SHA，新GPU Notebook在模型启动前核对该门及源码哈希。

可支持的结论：原先遗漏的Runner路径现在已覆盖，C1在**官方CPU模拟传输路径**兼容。它没有证明模型遵从契约指令，更没有证明修复成功率提高。
