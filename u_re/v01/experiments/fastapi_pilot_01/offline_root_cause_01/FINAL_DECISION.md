# 最终 Q1–Q12

**根因：MIXED_CAUSES。目标 API 缺失已确认；当前离线环境恢复仍被阻断。**

|问题|结论|证据|
|---|---|---|
|Q1 Issue要求什么？|新增yield dependency的function/request scope，分别在响应前/后退出；lifespan只是未来计划。|ISSUE_ORIGINAL.txt；ISSUE_CONTRACT_ANALYSIS.md|
|Q2 scope=function属于目标？|是，正文明确写出；两个失败调用与之匹配。|evaluator_test_text/tests/两份scope文件:23/26|
|Q3 两项TypeError归因？|TARGET_FEATURE_ABSENT；冻结实际工作区函数无scope/**kwargs，非误导入系统FastAPI。|DEPENDS_SCOPE_ANALYSIS.md；STATIC_FINDINGS.json|
|Q4 inline_snapshot缺失原因？|测试依赖未供给：subprocess跳过测试依赖安装，adapter仅装build/editable，批准资源没有该包。|INLINE_SNAPSHOT_DEPENDENCY_AUDIT.md|
|Q5 是否已声明？|是，requirements-tests.txt:13为inline-snapshot>=0.21.1；runtime extras不包含它。|base_source/requirements-tests.txt；DEPENDENCY_MATRIX.json|
|Q6 离线恢复方案？|当前41官方+124任务wheel无匹配；Requires-Python/ABI/传递闭包未知，不得声称版本不兼容或恢复可行。|DEPENDENCY_MATRIX.json|
|Q7 三错可分开？|可以：两项目标功能错误、一项独立环境错误。反事实为静态推论，未执行干预。|COLLECTION_ERROR_CAUSAL_ANALYSIS.md|
|Q8 原始证据一致？|exit2/JUnit3errors/任务身份一致。前后1191项哈希一致、ledger=true；PR15缺失/false的文字错误在本轮勘误，历史不改。|BASELINE_EVIDENCE_AUDIT.md；SOURCE_BYTE_VERIFICATION.json|
|Q9 V1是否过严？|缺少目标导致collection失败的归因，会排除合法新增API任务；但本次混合错误STOP仍正确。|ADMISSION_V1_CRITIQUE.md|
|Q10 V2如何定义？|Issue/base/trace/import/不变测试/原验证路径证据齐备且无环境缺失；仅CONDITIONALLY_ELIGIBLE，不能自动正式准入。|ADMISSION_V2_DRAFT.md；test_audit.py|
|Q11 值得新CPU吗？|现在不值得相同重跑。需批准兼容artifact及传递闭包、新环境方案、新V2开发注册和单独CPU授权。|CPU_NEXT_EXPERIMENT_PROPOSAL.md|
|Q12 是否零新执行？|是，零Kaggle API/SaveKernel/Notebook/GPU/Gemma/Agent/Submission；仅静态读取与8项自有离线审计测试。|OFFLINE_TESTS.log；EXECUTION_BOUNDARY.json|

旧CPU02保持CPU_TASK_ADMISSION_BLOCKED：0项准入，其余49项NOT_RUN。U-RE候选不变；没有算法收益证据。下一阶段GPU为No-Go。缺失包artifact兼容性、传递依赖和实际runtime pytest版本仍未知；没有额外wheel下载或安装。所有输入与报告SHA见INTEGRITY_MANIFEST.json。
