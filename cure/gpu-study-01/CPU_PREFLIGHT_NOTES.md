# CPU预检记录

预注册协议/任务/运行时及B/C候选保持不变。首次CPU预检中原有63项通过；新增Phase2测试的首题实际resolved=true，但测试驱动跳过了Agent sandbox启动，持久化观察器误将Verifier认作首个Agent sandbox，导致缺少phase2_execution.json。随后在同一Python进程复用worker，已关闭的FileHandler仍挂在logger上，临时目录删除后触发FileNotFoundError。此时没有GPU推理。

修正仅在**CPU测试驱动**：为脚本化Phase1创建并清理真实Agent sandbox以保持身份，每题使用独立Python进程，完整保存真实Verifier输出。它与正式研究supervisor每任务独立进程的方式一致；不修改冻结worker/r12，也不改变GPU运行的候选、任务、预算或session源码。采用新CPU Notebook ID cpu-r02，首轮失败档案保留，不覆盖。

最终CPU状态以各轮collection、study.log和study_cpu_gate.json为准。GPU首对必须在CPU-r02实际通过后才能启动；此次修复不构成任何模型尝试或结果筛选。
