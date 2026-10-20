# 正式评分快照

实际查询结束：2026-10-20T06:35:46.505182+00:00（北京时间 2026-10-20 14:35:46）。
API：competition_submissions / ListSubmissions；HTTP 200。没有新增提交请求。

| 候选 | Submission ID | 官方提交时间 UTC | API 状态 | Public Score | errorDescription |
|---|---|---|---|---|---|
| S0 | 57261002 | 2026-10-16T08:04:50.013Z | COMPLETE | 0.13 | null |
| 冻结 S2-T500 | 57402336 | 2026-10-19T16:20:56.950Z | PENDING | null | null |

S2-T500 尚不能与 0.13 作分数差值比较。EarlyEGV 没有正式成绩，也没有真实 Gemma 运行结果。
API 另返回 totalBytes=0、fileName、提交描述、提交者、队伍及保存版本 URL；完整原生字段在
[submissions_raw.json](submissions_raw.json)，未加工 HTTP 响应在 [wire_ListSubmissions.json](wire_ListSubmissions.json)。
没有返回 scorer 日志、错误堆栈、评分开始时刻、排队位置或任务进度。
不能凭持续时间、totalBytes=0 或用户界面的 Scoring 字样推断失败。
rich_3471 的单题 resolved=true 不是榜单成绩。

历史快照保持原样；这些文件是新的时间戳目录内观察，不替换旧状态文件。
