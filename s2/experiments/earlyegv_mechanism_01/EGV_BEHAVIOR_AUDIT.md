# EGV行为审计：未观察到自主委派

四份nested_audit.jsonl中，egv_verifier工具开始事件、子Agent模型开始事件和子Agent工具事件均为0。
HTTP Main工具schema请求数依次为61、62、31、25，共179；全部包含egv_verifier。
其余15个HTTP请求为不带工具schema的压缩等请求，不误算为子Agent。
因此不是“schema完全缺失”的已知CPU兼容故障；真实Gemma在本次合法工具选择中没有委派。
子Agent权限和共享预算的CPU证据保留，但不能声称本轮GPU已实际压力验证子Agent取消/副作用/500秒边界。

|问题|A两题|B两题|
|---|---|---|
|实际EGV调用|0|0|
|EGV真实行为断言|无|无|
|可操作EGV反证 / 交付 / Main处理|0 / 0 / 0|0 / 0 / 0|
|EGV引起的Main生产修订 / 成功复验|无|无|
|有效EGV闭环率|分母为0，null|分母为0，null|
|首次委派、委派预算、Patch前后位置|N/A|N/A|

无可评级的EGV反证，证据等级为N/A，不能把模型总结或Main自己的探针记作EGV结果。

Main的直接行为需要另行区分：

- Rich B：nested_audit 35–40创建并运行add_note探针，79–92对比标准traceback；95–104完成三处生产改动。
  之后多个reproduction/test_notes_capture脚本失败来自错误API调用或脚本假设，Main修改的是诊断脚本，未再修改生产文件。
  这不是“EGV反证→Main修订→成功复验”闭环。打印实际渲染有Level2行为信息；仅打印__notes__类型/提取字段为Level3。
- Rich A：179–192的自编探针先用无效show_traceback参数失败，再修正脚本并打印；直接将__notes__设为字符串，未覆盖add_note产生列表的常规路径。
  B在223–224真实显示Python3.12的__notes__为list。A对列表notes的兼容性是未实测风险，不能因21项原生测试通过就宣称所有契约已覆盖，也不能把尚未实测的风险重写为官方失败。
- FastAPI B：43–48按Issue将本地测试期望同步为Apache-2.0后执行pytest，两条断言测试通过，包含既有/items/行为。
  这是Main的实际验证，不是EGV；改变后的本地测试不能冒充原封不动的回归套件。最终官方提交过滤了测试文件，原生Phase2在新sandbox独立通过。
- FastAPI A：没有Agent主动测试命令，只有源码/文档搜索和diff；独立原生Phase2随后通过。

来源限制：Rich的import_audit记录工作区rich.traceback路径、源码SHA和模块代码执行，但模块被执行本身不证明行为断言通过。
FastAPI B pytest命令对应import_audit/68a289dfe35e4d61a3499c5ccb61f3c5/2453-exit.json，确认cwd、sys.path及工作区fastapi包。
冻结观察前缀仅fastapi，未单独记录被修改docs_src模块的__file__；测试import源码、工作目录、目标响应和最终Native Phase2提供强间接来源，不能伪造直接docs_src来源记录。

四臂get_status次数均为0，无证据证明模型按软检查点主动查询剩余预算。
0委派不能单凭本样本证明模型永远不会协作；两题可以被Main完成，且允许合理跳过委派。但本实验没有验证H1独立反证或H2反馈修复，也不支持H3净收益提升。
