# Formal submission 57402336: runtime exceeded, no score

Read-only Kaggle ListSubmissions query at 2026-10-20T09:43:39.715376+00:00 (17:43:39 Beijing). No new submission, Notebook save, GPU start, or candidate change.

| Submission | SDK/API status | errorDescription | Public Score |
|---|---|---|---|
| 57402336 / frozen S2-T500 | COMPLETE | Submission notebook exceeded allowed runtime | null |
| 57261002 / S0 | COMPLETE | null | 0.13 |

The exact official error is retained in `FORMAL_STATUS_RAW.json`. `COMPLETE` describes the terminal processing state here; the non-empty error and absent score mean this was not a successful scored submission. Do not convert null into zero, infer a partial leaderboard score from public-task passes, or claim that S2-T500 surpassed S0.

The response does not identify the failing stage, per-task timing, completed-task count, or evaluator log. It therefore confirms a formal runtime failure but does not establish that the 500-second cap alone caused it, that AgentTool was incompatible, or that the two-task research run failed. The packaging Notebook had completed previously; its success did not certify the downstream private scoring job's runtime.

The preserved T500 GLOBAL_BUDGET_MODEL.md already records both the 12-hour patch-production budget and the potentially distinct platform runtime window. A 500-second ceiling can consume 43,000 seconds over 86 full-cap tasks before any sandbox preparation; this is arithmetic sensitivity, not a statement about the actual hidden task count or this failure's precise cause. CPU/native single-task compatibility and two selected research pairs do not validate total hidden-workload throughput.

Disposition: formal S2-T500 promotion No-Go; no automatic resubmission. Keep S0's independently confirmed 0.13 baseline. Obtain actual stage/timing diagnostics if available, and separately validate a conservative whole-run completion envelope before spending another formal submission. Do not silently alter frozen candidates or treat a shorter cap as a proven remedy.

Historical PENDING snapshots and all original candidates, protocols, results, ZIPs and SHA manifests remain unchanged. This directory is a new additive observation outside the frozen experiment archive.
