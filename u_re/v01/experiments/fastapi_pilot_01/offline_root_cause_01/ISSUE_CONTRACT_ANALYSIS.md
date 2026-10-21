# 原始 Issue、base 与测试契约

任务为 fastapi_14262，base 为 425a4c5bb1d1a8e00007e82e5188fc4d30585767。ISSUE_ORIGINAL.txt 保存任务记录中 problem_statement 的原始 UTF-8 字节；SHA256 为 63bfaef6461b9744eaf3a4ff2a1961b752638263ba8bd5c413761f5412255102，与 CPU02 task_identity.json 一致。只提取 Issue、base、repo 和 evaluator test_patch；没有查看 reference/gold patch。

Issue 正文明示两个接口：Depends(func, scope="request") 为默认值；Depends(func, scope="function") 允许提前退出 yield dependency。正文定义 function 在路径函数返回后、发送响应前退出，request 在响应发送后退出。2025-10-03 编辑确认保留 scope、function、request 名称。标题对 request/提前退出的表述不够准确，不能用标题覆盖正文的明确区分。mode/response 是讨论中的替代名称；lifespan 是明确标注的未来计划，不是本题要求。

冻结 base 的公开 Depends 定义位于 base_source/fastapi/param_functions.py:2221，仅接受 dependency 和 keyword-only use_cache，没有 scope，也没有 **kwargs。内部 params.Depends 是 dataclass，仅有 dependency/use_cache 字段（base_source/fastapi/params.py:766）。这不是用当前最新版 FastAPI 代替旧版本：六个关键源文件/声明文件都与 CPU02 工作区前后哈希一致，七个下载文件的 Git blob 身份也已校验，见 SOURCE_BYTE_VERIFICATION.json。

测试覆盖来自原始 evaluator test overlay，SHA 为 0d7d188da3b72907ae6b9d09dd922f316cc374b8fa035ad1733ddec1142c77f3。evaluator_test_text/ 只是完整新增测试的静态文本，没有应用到任务工作区、也没有执行。HTTP 文件第23行和 WebSocket 文件第26行直接调用 scope="function"；HTTP 流式响应测试区分资源在响应发送时是否仍然打开。

原始 Issue 没有明确提到 WebSocket；WebSocket 生命周期属于评估测试对同一依赖 scope 功能的覆盖，不能改写成 Issue 的逐字要求。其测试检查消息处理期间资源打开、退出后关闭。第三个 tutorial 测试检查 /users/me 返回200及Rick。所有 evaluator-only 内容只保留在研究侧，不进入候选或未来 Agent 输入。
