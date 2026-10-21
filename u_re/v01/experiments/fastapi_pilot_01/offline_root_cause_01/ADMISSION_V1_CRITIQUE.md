# V1 的适用边界

原 SELECTION_PROTOCOL.json 没有改变。screen.py:24-37 的 decide 在证据完整时接受 assertion_failure，拒绝全通过的非区分基线，仅对已支持的 httpbin fixture 缺失作已解释拒绝；其他收集/设置错误 STOP。函数没有读取 Issue、base API 或目标因果关系。

这能保守拦截真实依赖、损坏证据和无法解释的错误，但不足以覆盖“新增 API”任务。fastapi_14262 两个模块级调用恰好使用 Issue 明确要求的新参数，base 尚不支持，因此测试必须在收集阶段失败。把“所有测试必须先成功收集”作为通用前置条件，会系统性排除这类合法代码修复问题。

收集失败可以是有效的修复前负面基线，但需要 Issue、base签名、报错位置、工作区导入身份共同建立目标因果关系，并排除独立环境问题。异常阶段、错误关键词或模型自述都不够。

这不使本次 CPU02 变成合格：独立 inline_snapshot 缺失依然阻断原始测试集合。因此原实验 STOP/CPU_TASK_ADMISSION_BLOCKED 保持正确；V2 只是改善归因能力，不是回填通过、换题或继续旧筛选的授权。
