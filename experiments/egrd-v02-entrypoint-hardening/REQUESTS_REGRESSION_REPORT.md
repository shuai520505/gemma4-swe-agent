# Regression results and limits

Read exact final exit codes in REGRESSION_EXECUTIONS.json and FOLLOWUP_EXECUTIONS.json. Required existing47, legacy27, infrastructure6 and four actual official Compiler package checks are rerun. New forensic/classifier suite has17 checks against original evidence, source binding and negative trust cases. These are CPU unit/process checks, not real fixture service acceptance.

| Requested capability | Actual coverage | Live service result |
|---|---|---|
| Requests source precedence |Existing source import subprocess test plus actual CPU02 Agent receipt/Native trace|Prior source binding observed; no new Linux run|
| Fixture provider availability / missing provider |All187 traces and59-wheel inventory checked|Provider resolution failed|
| HTTP startup |Exact failure-before-start evidence; provider source audited|NOT_RUN|
| HTTPS startup |Separate4 secure traces; TLS source audited|NOT_RUN|
| Fixture teardown |No invented teardown success; actual sandbox cleanup verified|NOT_RUN for fixture lifecycle|
| Port conflicts |No EADDRINUSE evidence; default port0/source reviewed|NOT_RUN|
| Proxy isolation |Explicit clean launcher environment checked|Source-verified; direct runtime env dump not available|
| Agent/Native parity |Same wheel hashes, shared command binding, source paths|Complete byte parity UNKNOWN|
| Abnormal fixture termination |No service was started; lifecycle not fabricated|NOT_RUN|
| Cleanup |Both original cleanup receipts checked; existing cleanup/process tests rerun|Original sandbox cleanup confirmed|

The gate for dispatch is not met: positive fixture service acceptance cannot be inferred from passing these forensic checks. Initial RED tests and the label-mismatch failure are retained, along with successful final reruns. No tests were deleted or weakened.

## Evidence identity and execution boundary

Generated UTC: 2026-11-03T15:07:52.529834+00:00. Audited PR46 source commit: `9ef032ab23335cb5a09c4937d7962205f5962f79`.

Task `requests_6589`, base `7a13c041dbef42f9f3feb14110f02626f6892e9a`, Issue SHA256 `60b61eb2b26e1135174dd59ddc4e29b2d7fe2b5e255b723e9085b36407663d04`, snapshot SHA256 `053f2ea73cb7b604f535ee2eabe596dae9df9d7ff54a365d62b4ff0bebab7115`. Package B SHA256 `9a8566523e4463889a6e8f61d7cb7e760fd48873ea9827e529b29c5abca6fa80`. Official evaluator swegemma0.2.11 source SHA256 `99e2a5fdab2be2b5e0388de29080da9d6e7003cf8b53299cda790464f4ecd2aa`; unchanged.

Original CPU02 archive: `cpu02-output/egrd-v02-cpu-hardening02.zip`, SHA256 `25b2a360c62023c48617fe8c3bb8734d4230a2d3668eccc33cb4e22f20fcf25a`. Raw records: `cpu02-evidence/worker/trusted/NATIVE_RESULT.json`, `native-junit-0.xml`, `NATIVE_COMMANDS.json`; Agent/Native cleanup receipts and original session/done hashes retained. Full191 failure/error case identities, trace hashes and excerpts: `native-recovery/AUTOPSY.json`.

Commands/timestamps/exit codes: `native-recovery/REGRESSION_EXECUTIONS.json`, `FOLLOWUP_EXECUTIONS.json` and referenced logs. Actual prior Native pytest command is recorded verbatim in AUTOPSY.json; exit1. Prior worker stage exit0 did not imply trustworthy test execution. New CPU SaveKernel0, GPU SaveKernel0, Gemma requests0, packages installed0. Local tests validate classification/source evidence; they do not replace Native evaluation. New Linux service acceptance and Native revalidation are NOT_RUN.

## Final actual local results

| Check | Final result | Exact receipt |
|---|---|---|
| Existing47 |PASS, exit0|FOLLOWUP_EXECUTIONS.json / existing47_final.log|
| Legacy27 |PASS, exit0 (440.561s)|REGRESSION_EXECUTIONS.json / regression-logs/legacy27.log|
| Infrastructure6 |PASS, exit0|REGRESSION_EXECUTIONS.json / regression-logs/infrastructure6.log|
| New17 forensic/classifier checks |PASS, exit0|FOLLOWUP_EXECUTIONS.json / fixture17.log|
| Actual Compiler A/B/C/D |PASS, exit0|REGRESSION_EXECUTIONS.json / compiler-work/evidence/SDK_COMPILER.json|

The initial aggregate test runner exited1 because it retains the earlier fixture-status-label failure; the final individual follow-up checks exit0. Its original failure log is preserved. No full legacy suite was rerun to hide that history. FINAL_CHECKS.json records the final ledger and exact package/task/snapshot/evaluator identity checks.
