# 下一次 CPU：当前 No-Go，不做相同重跑

当前为 ENVIRONMENT_RECOVERY_BLOCKED / OFFLINE_DEPENDENCY_RECOVERY_UNAVAILABLE。静态证据已足以证明 scope 参数缺失；不需要再用 CPU 重复证明。另一次相同环境执行也不会生成批准清单里不存在的 inline-snapshot。

申请新CPU计算前至少需要：

1. 官方或另行明确批准的 offline inline-snapshot wheel，满足>=0.21.1，绑定SHA、Python3.12兼容的Requires-Python/标签以及完整批准传递依赖。目前这些artifact不存在，兼容性不得假定。
2. 新的、经审查的离线测试依赖准备方案。可修改范围仅限获准的研究环境适配，不改任务源码、原测试、Verifier；不能把研究workaround冒充官方评分环境修复。
3. 独立的V2开发实验编号、源码/测试覆盖物/模型候选身份、证据谓词和STOP；保留原Pilot阻断。
4. 记录实际解释器/pytest/依赖版本、sys.path、模块来源、before/after哈希、原始JUnit/TaskResult和清理。

若以后单独获授权，最小开发验证可以仅一次 CPU-only：先做环境导入/metadata检查，再对未改动 fastapi_14262 执行原始 verify_task、空patch和原测试集合。预期应消除独立依赖错误，而目标API错误仍然可能存在；这只是待检验假设，不能预先保证只剩两错或完成收集。出现新未知错误即STOP，不继续旧协议的49题。

纯规划预算：准备300秒、原生Verifier300秒、导出/清理180秒、安全120秒，加平台启动余量300秒，共1200秒。未请求此窗口，也未测得这些耗时。历史CPU02 TaskResult12.61秒、pytest0.98秒不保证未来时间。没有批准artifact前不建议花费新CPU资源。

开发验证通过后，才可考虑新的49题机制研究预注册；GPU仍需独立资源、模型、请求、完整窗口和人工执行授权。本轮没有任何新计算。
