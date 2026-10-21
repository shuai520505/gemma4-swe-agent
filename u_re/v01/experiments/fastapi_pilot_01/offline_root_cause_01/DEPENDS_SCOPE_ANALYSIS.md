# 两项 Depends(scope=...) TypeError 的归因

| 项目 | HTTP | WebSocket |
|---|---|---|
|静态测试文件|evaluator_test_text/tests/test_dependency_yield_scope.py.txt:23|evaluator_test_text/tests/test_dependency_yield_scope_websockets.py.txt:26|
|调用时机|模块级 Annotated 别名，pytest 导入期间|同左|
|调用|Depends(dep_session, scope="function")|同左|
|根因分类|TARGET_FEATURE_ABSENT|同一目标 API 缺失|

测试均从 fastapi 导入 Depends；base_source/fastapi/__init__.py:14 将其从 param_functions 导出。公开函数在 param_functions.py:2221，省略长注解文档后的结构签名为 Depends(dependency=None, *, use_cache=True)。没有 scope，没有 **kwargs；其返回值在第2278行构造 params.Depends。内部 dataclass 从 params.py:766 开始。

这不是意外导入系统 FastAPI。原始 import_audit/3cfb8d83126b467e940219b6e32aa62e/130-exit.json 记录了 fastapi.param_functions、fastapi.params 的实际 workspace 路径、源文件 SHA 和模块代码执行。公开函数文件 SHA 为 e31e98e713a3166ba32e76cc0d7c6f17e91dafe975999d1b48e4c32e81d88fa4，内部 params 文件 SHA 为 e5c224c4490ec58bb98ee9cd8a5c48e94661a086da6aae648e1018dabbeb838f，均匹配冻结 base 和运行前后快照。editable 安装日志显示从系统0.136.1切换到工作区0.120.4，但真正排除误导入的是路径/字节证据，而非版本打印。

Issue 明确要求新参数；测试直接使用该参数；实际执行的旧函数不能接受它。三条独立证据支持 TARGET_CAUSED_COLLECTION_CONFIRMED。不能仅因异常发生在 collection 就称为环境错误。现有记录也没有证明这两个具体异常来自 Python/pytest 版本冲突；实际 pytest 版本未被记录，不能据此认证整个环境兼容。

反事实仅为静态推论：正确支持目标契约后，这两个确切的参数绑定错误应消失；只添加参数并不证明后续 yield 生命周期、依赖图、流式响应或 WebSocket 行为正确。后续仍可能出现其他错误或断言失败。本轮没有实现修复，也没有重新运行测试。
