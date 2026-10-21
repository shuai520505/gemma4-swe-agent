# 三项错误的独立因果关系

|错误|发生阶段|有证据支持的原因|
|---|---|---|
|HTTP Depends(scope) TypeError|模块导入/收集|Issue 要求的新 API 在实际 workspace base 中尚未实现|
|WebSocket Depends(scope) TypeError|模块导入/收集|同一个 API 契约在另一使用场景中缺失|
|inline_snapshot 导入失败|模块导入/收集|与生产修复目标独立的测试依赖未供给|

总分类为 MIXED_CAUSES。JUnit 的 collection_error 是阶段描述，不是根因。没有 Agent 执行，不能将任一项记作 Agent 引入的回归。

以下是静态反事实，不是执行结果：安装 inline-snapshot 不会改变旧 Depends 签名，因此不会消除前两项错误；正确实现 scope 也不会使第三方测试工具自动可导入，因此第三项仍可能阻断。两项 TypeError 是同一个缺失接口，不是两个独立任务或两个独立修复样本。

inline-snapshot 是快照测试辅助依赖；本题生产目标是 yield dependency 生命周期。虽然两者无直接实现关系，原始 evaluator 测试集合仍会通过 tests/utils 导入该依赖，不能删掉这段导入来绕过环境。

旧 CPU02 继续 CPU_TASK_ADMISSION_BLOCKED。V2 若只看到前两项，可考虑 CONDITIONALLY_ELIGIBLE；当前还有独立环境错误，整体仍须 ENVIRONMENT_BLOCKED。任何一层问题消失后是否还有隐藏问题，尚未执行验证。
