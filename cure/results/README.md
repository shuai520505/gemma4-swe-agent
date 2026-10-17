# 原始证据索引

所有运行均为CPU，无真实Gemma生成、GPU实验、训练或Kaggle正式评分。

| 运行 | 结果 | 原始证据 |
| --- | --- | --- |
| cpu-r01 / Kaggle版本1 | ERROR；原有38项通过，候选目录内ZIP导致新增官方编译失败 | [evidence.zip](cpu-r01/evidence.zip) |
| cpu-r02 / Kaggle版本1 | COMPLETE；38+23项通过 | [evidence.zip](cpu-r02/evidence.zip) |
| cpu-r03 / Kaggle版本1 | COMPLETE；38+25项通过，18组HTTP参数子案例通过，0跳过 | [evidence.zip](cpu-r03/evidence.zip) |
| local-mechanisms-r01 | 12条真实CPU脚本重放；非模型修复率 | [原始包](local-mechanisms-r01.zip)、[汇总](local-mechanisms-summary.json) |

[前两轮索引](cpu-evidence-index.json) 和 [最终索引](cpu-evidence-final-index.json) 记录下载档案SHA256、字节数、Notebook ID/保存版本和实际状态。每轮 `archive-members.json` 给出原始ZIP内逐文件SHA256；同目录可读日志是原始成员的逐字节副本。CPU gate包含实际依赖版本和所测源码哈希，HTTP案例明确使用mock响应。

`preservation-r01.json` 是本机初次检查；`preservation-final.json` 是交付前再次检查，验证76项冻结文件、28项r12源码、旧S0/正式实验ZIP与所有原有Git跟踪文件不变。`delivery-manifest.json` 记录交付文件（自身除外）的SHA256。历史CPU门作为当时证据保留；只有匹配当前源码的最终cpu-r03门可用于当前研究运行。

原生运行时间保留UTC，不将次日整理时间改写为实验时间。局部CPU耗时不等于模型推理成本；缺少官方最终结果时不写成官方failed。
