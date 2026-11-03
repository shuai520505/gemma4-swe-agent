# Worker and aggregate contract

Each session owns a new output directory. Worker persists SESSION_RESULT.json (EGRD_SESSION_V2), CLEANUP.json (EGRD_CLEANUP_V2), then worker_done.json (EGRD_DONE_V2) last. Done binds session ID, OS exit expectation, result SHA, cleanup SHA and Native result SHA. Aggregate uses AGGREGATE_RESULT.json (EGRD_AGGREGATE_V2) with the same cleanup/done convention and hashes of every planned child supervisor receipt.

OS exit/process-tree state remain authoritative. A success-looking done file cannot override nonzero exit, a live process, missing data, mismatched hashes or failed cleanup. The concrete legacy supervisor audit is retained separately; no artificial official_result.json is fabricated to satisfy its obsolete normalizer.

| Observed condition | Result / continuation |
|---|---|
| Agent completes, Native SUCCESS resolved false | ordinary failed repair; continue |
| Exact SDK deadline, fallback/no patch, Native completes and cleanup confirmed | AGENT_TIMEOUT; retain and continue |
| Worker nonzero exit | WORKER_ABNORMAL_EXIT; stop |
| Outer/stage cap expires | WORKER_TIMEOUT; stop |
| Native missing/error, JUnit setup/runtime errors, missing/empty/all-skipped report or abnormal exit | NATIVE_EVALUATION_FAILED; stop |
| Cleanup incomplete or process tree remains | CLEANUP_FAILED; stop |
| Missing result/cleanup/done | RESULT_MISSING or abnormal exit; stop |
| Identity/schema/hash mismatch | RESULT_CONTRACT_INVALID; stop |
| Aggregate missing a planned child or child trust failure | stop; suffix NOT_RUN |

Cleanup failure takes precedence when confirmed even with nonzero exit. For missing receipts no success is inferred. Native UNKNOWN stays null. Aggregate engineering activation metrics are distinct from Native repair results and from permission to use GPU.

CPU tests cover JSON contract boundaries and actual inherited process supervision using owned child-process fixtures. Fixture Native receipts test plumbing only, not evaluator execution. The separate worker_cpu stage uses the actual official Native Evaluator on a public Requests snapshot and a comment-only negative-control patch.

CPU02 exposed a weakness in the initial plumbing gate: raw resolved=false also covered187 fixture errors. Its historical PASS receipt is unchanged. The final trust guard checks actual Native JUnit and refuses continuation;47 local tests pass. The final guard itself is not Linux-revalidated, and no public repair/environment success is claimed.
