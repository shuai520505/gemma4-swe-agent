# 正式配对实验 01：执行结果与限制

**执行已结束，实验不完整。不能报告完整 V0/V1 修复率，也不能判定 V1 优于 V0。** 原计划8次，实际执行7次：6次取得完整失败判定、1次unknown、1次not_run。没有将缺失项当成确认失败，没有拼接Pilot或其他轮次，也没有为凑满而补跑。

## 冻结协议与实际执行

实验ID：harness-v2-formal-paired-01；冻结提交8bbf6e2；Harness 2.0.3/r12。protocol.json SHA-256为ac0921507cbd970f3f7c2cc859dd456612fe3ca72e24b38b8a4617db042daae4。4道新题来自4仓库，按seed20261016随机排列；块内交替候选顺序，拆成两个独立Notebook。源码、ZIP、Issue/base和Notebook哈希均在执行前注册。

两批复用CPU38项及GPU验收通过的r12运行时，8分钟/60工具，命令120秒、Verifier300秒、外层1530秒。31B v2、六工具、单Agent、冻结Prompt不变；相同官方wheel字节哈希在安装前核验。不是S0的5分钟提交预算实验。

批次A保存版本v1：[Notebook A](https://www.kaggle.com/code/wudangdexiaodoashi/gemma4-formal-paired-01-a)。批次B保存版本v1：[Notebook B](https://www.kaggle.com/code/wudangdexiaodoashi/gemma4-formal-paired-01-b)。二者均COMPLETE，但A按预注册unknown停止策略只执行3题次。原始CPU/模型服务、上下文探针及逐题证据另存于原始ZIP。

## 逐次结果

| 任务 | 候选 | 审计状态 | 原始Phase 2 | LLM / 工具 | 控制器秒 | 可观察ADK tokens |
| --- | --- | --- | --- | --- | --- | --- |
| requests_7309 | v0 | failed | 6 failed, 201 passed, 13 skipped in 0.40s | 34 / 30 | 232.963 | 189348 |
| requests_7309 | v1 | failed | 6 failed, 201 passed, 13 skipped in 0.39s | 23 / 21 | 429.871 | 137651 |
| httpx_3672 | v1 | unknown | 无Phase 2；空Patch | 44 / 44 | 493.988 | 260746 |
| httpx_3672 | v0 | not_run | 未接纳 | — / — | — | — |
| rich_3052 | v0 | failed | 1 failed, 6 passed in 0.09s | 34 / 30 | 404.734 | 212594 |
| rich_3052 | v1 | failed | 1 failed, 6 passed in 0.09s | 55 / 55 | 497.414 | 350962 |
| fastapi_14258 | v1 | failed | 1 failed in 0.44s | 28 / 25 | 161.805 | 145007 |
| fastapi_14258 | v0 | failed | 1 failed in 0.44s | 45 / 45 | 498.463 | 258480 |

HTTPX/V1达到官方480秒Agent截止，保存的Patch为0字节；官方resolved=false、exit=-1并不构成实际验证失败，因此规范化unknown。工作进程和目录均已清理，但批次仍按预注册策略停止接纳，HTTPX/V0为not_run。没有外层控制器超时或清理污染。

Rich/V1和FastAPI/V0也达到Agent截止，但随后非空Patch的Phase2实际完成，故保留真实failed判定，原始超时error_message不删除。这与HTTPX缺失验证的情况分开记录。

## 观察指标

| 候选 | 平均LLM调用 | 平均工具调用 | 平均控制器秒 | Agent截止次数 |
| --- | --- | --- | --- | --- |
| v0 | 37.67（n=3） | 35.00（n=3） | 378.720（n=3） | 1 |
| v1 | 37.50（n=4） | 36.25（n=4） | 395.769（n=4） | 2 |

上述为已执行样本的描述，V0缺一题，V1含无判定HTTPX，样本不对称，不能据均值推断性能优劣。V0为3 failed/1 not_run，V1为3 failed/1 unknown；两组完整Resolution Rate均为null。3个完整配对均双失败，不能用这3个子集代替预定4题比较。

6次非空Patch均确认应用并启动验证；HTTPX空Patch没有验证。完整计划Patch有效率不报告，应用确认数为V0=3、V1=3。6次验证中没有测试收集失败（0/6），均exit1的断言/运行行为失败：Requests仍保留畸形参数；Rich的返回值或公开参数接口不满足测试；FastAPI抛出异常仍未通过原生用例。以上是输出支持的现象，不据此猜测参考Patch或宣称环境已排除全部影响。

## Token与证据完整性

7份原生TaskResult.total_tokens均为0，但对应ADK usage非零；原始字段不变，初版results.json保留该原始值。修订审计results-v2.json将这些占位零的可解释总tokens记null，另报告从实际ADK响应求和的observed_native_usage_tokens。这些值不包含未观察到的压缩usage，属于可观察下界，不能宣称完整消耗或零成本。新增回归测试验证占位零不会抹掉真实usage。

所有已执行项的冻结Prompt/模型身份、上下文准入、原生边界Trace、Patch版本、进程停止和目录清理通过检查。完整失败项均有Phase2输出。HTTPX的边界Trace和空Patch保留，缺失Phase2明确标出。未执行项没有伪造Trace、工具计数或Patch。

原始ZIP：

- A：480898字节，SHA-256 a0b114193b76f4d8fa6f905c0956a26d5f427d6a5e4ed6dff3a1e4ec62b4e4e6。
- B：672629字节，SHA-256 e0c0548bd309fd87c0b8d294c9df7c1526138c510e128af09f7ff4094cb1f436。

CRC、manifest和每批28项注册源码核验通过，原始V0及76项Pilot保护清单未变。只读ZIP审计在harness_v2/results/paired01-{a,b}-gpu-audit.json；原始Phase2、Patch及Trace成员哈希索引在docs/validation/formal-paired-01/。完整ZIP/Trace在本机artifacts/formal-paired-01与私有Kaggle输出保留。

冻结r12 run_batch输出的audit_summary沿用development-only标签及null rate，未修改运行时来迁就报告；本正式分析从原始TaskResult和冻结协议另算。该兼容性限制已在执行前注册。

## 决策

本轮不提供赢家，不补历史结果凑满。先保存S0首次正式提交的实际分数锚点；公开高分方案研究另见PUBLIC_LEADERBOARD_STUDY.md。后续策略或预算改变应建立独立候选和新协议，使用未暴露答案的新任务，避免对这四题反复定制。本项目尚无本轮有效完整对照证明V1增益。
