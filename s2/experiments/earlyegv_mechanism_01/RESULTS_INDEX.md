# 完成结果入口

唯一研究Notebook：[gemma4-s2-earlyegv-mechanism-01](https://www.kaggle.com/code/wudangdexiaodoashi/gemma4-s2-earlyegv-mechanism-01)，保存版本1，COMPLETE。

- [结果与Q1–Q15](GPU_RESULTS.md)
- [官方配对与成本表](PAIR_COMPARISON.md)
- [EGV真实行为审核](EGV_BEHAVIOR_AUDIT.md)
- [源码改动时序](PATCH_TIMING_AUDIT.md)
- [显式提交、重复提交与诊断残留](CLOSURE_AND_SUBMIT_AUDIT.md)
- [Go/No-Go和后续边界](EXPERIMENT_DECISION.md)
- [可复算测量](ANALYSIS_MEASUREMENTS.json)、[四运行账本](GPU_RUN_LEDGER.json)、[启动/压缩/角色Token口径](MODEL_USAGE_SCOPE.json)
- [完整原始归档](results/gpu01/raw.zip)、[CRC/清单核验](RAW_COLLECTION.json)、[最终SHA清单](INTEGRITY_MANIFEST.json)
- [实际4L4与执行环境](results/gpu01/gpu_runtime_admission.json)、[完整运行门](results/gpu01/batch_gate.json)、[服务进程清理](results/gpu01/server_cleanup.json)
- [配额前](GPU_QUOTA_BEFORE.json)、[配额后原始HTTP](GPU_QUOTA_AFTER_RAW.json)、[配额后解释](GPU_QUOTA_AFTER.json)
- [正式状态收尾查询](FORMAL_SCORE_STATUS_FINAL.json)，与[预检查询](FORMAL_SCORE_STATUS.json)分别保留。

预注册来源：[README](README.md)是未改写的保存前记录；[授权](GPU_AUTHORIZATION.json)、[执行构建](EXECUTION_BUILD_MANIFEST.json)、[保存前清单](PRELAUNCH_INTEGRITY_MANIFEST.json)同样保持原值。
这些文档中的“pending/not_run”是注册时状态，不替代本页链接的实际完成账本。

候选与原GPU草案未改。只有新的授权执行副本被保存/运行一次；源码在首次推理前由131e732封存，回执11e2a3c、早期运行记录9736950。
新报告和分析脚本不在Agent ZIP或实际执行载荷内。

两个样本均A/B成功，0次EGV委派。这个结果不能当作Kaggle正式分数、总体100%修复率或双Agent优势。
