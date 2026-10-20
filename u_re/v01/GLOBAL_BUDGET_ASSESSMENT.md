# Whole-run risk is a P0 gate

S2-T500 formal57402336 returned COMPLETE with a non-empty runtime-exceeded error and Public Score=null in the preserved9aed40f API snapshot. COMPLETE there means terminal processing, not a valid score. The response did not expose task counts, per-task times or a failing stage. It cannot establish that500s alone, EGV or a repeated-edit loop caused the failure. CPU compatibility and a few public successes never certified private full-run throughput.

This assessment carries forward the stated competition12-hour patch-production allowance (including sandbox setup, excluding native verification). The evaluation page returned no readable body and Code Requirements was inaccessible to this turn's web reader; no fresh precise platform-window rule is claimed from that access attempt. Official public HARNESS_README documents per-task eval_config overrides, native budgeting and termination, not the unavailable private scorer schedule. Reconfirm current whole-submission limits before any formal submission. The12h patch clock, Notebook/platform clock, per-task deadline and native verification timeout are separate quantities.

budget.py creates360 deterministic sensitivity rows, not fitted distributions or success probabilities. Task counts60/80/100/120/140, ordinary Agent duration90/180s, full300s-cap fraction25/50/75/100%, setup5/20/60s, post-Agent lifecycle10s, bootstrap1200s, export900s and native verification30/120/300s are explicitly assumed. Repair tests, diff and submission already lie inside Agent time; post-Agent teardown/persistence does not double-count them. A600s patch-clock safety reserve is included. No concurrency speedup or two-task S2 latency distribution is assumed.

| Task count | Maximum mean Agent+setup with600s reserve | Agent mean if setup20s | All300s+20s setup+reserve |
|---:|---:|---:|---:|
|60|710.00s|690.00s|19800s|
|80|532.50s|512.50s|26200s|
|100|426.00s|406.00s|32600s|
|120|355.00s|335.00s|39000s|
|140|304.29s|284.29s|45400s: exceeds12h|

With120 tasks and60s setup, all300s cases plus reserve reach43800s and also exceed12h. A lower per-task ceiling reduces cap-heavy risk but does not guarantee full completion, correctness or prompt ending after submission. Actual cancellation/cleanup latency may extend platform time beyond300s; measured CPU Mock durations do not quantify the Gemma tail.

CSV reports both platform branches: verification outside the Notebook window, or serial verification inside it. Without known scheduling and an actual platform limit, platform_fits stays UNKNOWN. Native Phase2 remains complete; it is never shortened to make a scenario fit. Bootstrap and export are not assumed free. Exact official private validation placement must be verified, not guessed from the earlier timeout.

Required new measurements: U-RE Agent and Worker P50/P90/P95, cap fraction, explicit successful-submit fraction, delay after first successful submit, native setup/cleanup/export durations, verification time and scheduling, actual meaningful EGV-check/revision duration, useful-revision fraction, received HTTP usage completeness, and total attempt cost per officially resolved task. With zero successes, cost per success is undefined. Do not infer population tails from two selected S2 tasks or scripted toy cases.

Formal submission is NO-GO now. Further No-Go conditions include failed CPU or integrity gates; unresolved private timing/clock placement; insufficient representative U-RE throughput data; a conservative full-workload bound exceeding the confirmed limit minus safety reserves; unbounded observed post-submit/no-progress behavior without an acceptable completion envelope; incomplete cleanup/HTTP/Verifier evidence; or unknown hidden-count range without an adequate sensitivity bound. An assumed scenario frequency is not a calibrated timeout probability. No formal submission or new scoring Notebook is created here.
