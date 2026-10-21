# U-RE-FASTAPI-ADMISSION-V2-DRAFT

仅草案；execute=false；不覆盖 V1，不修改官方 Harness/Verifier，不注册可运行任务。

先逐项分类，再聚合任务：

|类别|证据要求|状态|
|---|---|---|
|A TARGET_BEHAVIOR_FAILURE|真实行为断言失败且身份/结果完整|负面基线候选|
|B TARGET_CAUSED_COLLECTION_FAILURE|Issue明确契约、base缺失、错误直接发生于目标使用处、工作区来源证明、测试/Verifier未变、无独立环境缺失、有原生修复后验证路径|仅 CONDITIONALLY_ELIGIBLE|
|C ENVIRONMENT_COLLECTION_FAILURE|独立测试依赖/provider不满足，由声明、安装/导入和artifact证据证明|环境恢复前阻断|
|D UNEXPLAINED_COLLECTION_FAILURE|证据不足、冲突或无法归因|STOP|

每个条件必须保存真实路径、行号、SHA；不能只填写模型给出的布尔值。任务聚合优先级为完整性失败STOP、任意未知原因STOP、任意环境原因BLOCK、纯目标收集失败CONDITIONAL、正常行为负面基线候选。不能用B覆盖同时存在的C。

B不能自动升级 BASELINE_ELIGIBLE。后续需要独立的契约/源码审查、新注册的CPU环境验证，证明依赖可用、源码来源、原始测试端点、结果落盘及清理有效；晋级仍须单独协议决策。不得用参考修复、伪造fixture、删测或改断言建立证明。

未来任何新CPU结果出现前，先冻结分类源码/证据谓词、新排除表、原相对排序、最多8次检查、已解释环境拒绝后的处理及全局UNKNOWN/完整性STOP。所有任务应用一致规则，不按修复结果临时放宽。

audit.py 的 event_category/draft_admission 仅演示这些离线规则；8个自有测试验证谓词缺失、混合错误优先级和条件状态不会自动晋级。它没有替换 screen.py、没有安装进官方评分路径，也不是实际任务准入控制器。
