# CURE Mechanism 02 / C1

独立于已停止的study01。冻结C1只修复ADK字面标记，不修改算法或B/S0。

- [最终对照报告](../GPU_MECHANISM_C1_RESULTS.md)：A兼容通过；B仅部分状态表达，主动反证改向未证实；C无修复率提升证据。
- [候选精确Diff](candidate-exact.diff)、[新旧SHA](candidate-derivation.json)、[C1 ZIP](../packages/cure_v01_c1/submission.zip)。
- [CPU完整Runner结果](C1_COMPATIBILITY.md)：63+5项通过，旧C和双花括号为预期失败。
- [预注册协议](PROTOCOL.md)、[机器协议](protocol.json)、[实际结果](summary.json)、[独立于自报的机制判断](mechanism-assessment.json)。
- [工具逐事件记录](TOOL_TIMELINE.md)、[原始GPU档案](results/smoke/evidence.zip)、[原始CPU档案](results/cpu/evidence.zip)、[完整性检查](integrity-audit.json)。
- [保存的GPU Notebook](notebooks/smoke/study.ipynb)、[CPU Notebook](notebooks/cpu/study.ipynb)：含冻结源码bundle，无自动正式提交入口。CPU metadata初次标题被Kaggle规范化，实际执行ID以collection为准；修改ID会产生新的运行，不能当作原证据。

本轮新B/C1各运行一次，两者真实Phase2均2 passed，最终Patch相同。场景已被观察过，属于探索性兼容/机制验证；没有将合成任务计入Kaggle Resolution Rate，也没有新增正式提交、LoRA或扩展实验。

注册JSON的not_executed表示**登记时**状态，保持不可变；实际执行状态在results/collection、batch_gate和summary。交付SHA见 [delivery-manifest.json](delivery-manifest.json)。
