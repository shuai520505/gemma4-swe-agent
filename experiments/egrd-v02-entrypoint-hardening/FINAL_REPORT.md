# EGRD V0.2 final report

**Status: BLOCKED_INFRASTRUCTURE.** The three requested engineering fixes are implemented, but independent Native evaluation still has fixture setup errors. GPU authorization is present; no GPU was dispatched because the CPU trust gate is not satisfied.

## Actual evidence

Two independently confirmed CPU-only Kaggle runs completed, each with one SaveKernel and no retries, GPU/TPU disabled and no model mounts:

| Run | Evidence |
|---|---|
| CPU01, version1 | Original27 + infrastructure6 + new39 tests, four official Compiler packages, SDK clock and actual nonroot Skill PASS; Requests Worker stopped before model request because imports resolved to /opt/approved instead of locked src-layout source |
| CPU02, version1 | Original27 + infrastructure6 + new43 tests, Compiler4, SDK clock, nonroot Skill and Worker plumbing PASS; actual Native execution returned4 failed,131 passed,2 skip/xfail,187 setup errors |

CPU01 archive SHA256: `06d1a057fb5f5d4f7a9effd18b9d569cdef2bf1b8326b03e2f03368642121723`.

CPU02 archive SHA256: `25b2a360c62023c48617fe8c3bb8734d4230a2d3668eccc33cb4e22f20fcf25a`.

Both platform statuses are COMPLETE. CPU02's raw CPU_SUMMARY says PASS because the original plumbing assertion required Native resolved=false, which also occurs with setup errors. That original receipt is preserved unchanged. Independent inspection of the raw JUnit found324 cases,187 errors (183 recursive httpbin fixture errors and4 httpbin_secure fixture errors), so **trusted CPU acceptance is FAIL**. This is not evidence of a valid negative repair control or of model failure.

The source binding is repaired for both Agent and Native commands with /workspace/src first. Real CPU02 receipts prove source import, init, comment-only edit and official submit. The comment patch is not a repair. Independent Native ran22.55s and raw resolved=false, but its environment is not trustworthy for repair evaluation. Cleanup is confirmed in both runs.

The latest trust guard now requires actual nonempty Native JUnit with executed cases and zero setup/runtime errors, in addition to original Native result/hash/exit checks. Missing/all-skipped/malformed evidence fails closed. It changes the research stop gate, not official scoring, expected tests or the raw resolved value. All47 current local tests pass, including actual child-process supervision and new Native-error/missing/empty/skipped cases. This final guard has not been rerun on Linux; that limitation remains explicit.

## Required answers

1. **EGRD on the execution path?** CPU_VERIFIED through actual official SkillToolset in a nonroot owned fixture. V0.2 real Gemma execution is NOT_RUN.
2. **Missing Skill calls fixed?** Real schemas and an explicit common FIRST ACTION prompt are integrated. CPU lifecycle passes. Whether Gemma obeys the prompt remains UNKNOWN.
3. **Hard controller or prompt?** PROMPT_ENFORCED_OPTIONAL_EXECUTION. No unsupported callback/middleware or global interception exists. Core checks act only when the Skill is invoked; infrastructure supervision is executable.
4. **Timing fixed?** The actual SDK timeout object is observed and Context aligned to its origin without changing300s. CPU boundary tests and actual SDK Skill sessions pass. GPU deadline cancellation remains NOT_RUN.
5. **Supervisor accurate?** Tests cover session/aggregate identity, hashes, process exit, Agent vs Worker timeout, Native failure, cleanup failure and missing data. The new trust guard rejects CPU02's actual187 errors. No successful official_result is fabricated.
6. **12B actual tool test?** NOT_RUN this version. Prior12B loading is historical, not new evidence.
7. **31B takeover?** NOT_RUN. Exact original config, independent Notebook/output/claim path and bounded fallback recommendation are prepared. A single repair failure is insufficient to switch; infrastructure failure cannot justify switching models.
8. **Real Patch Intent?** Yes in the scripted owned official-Skill lifecycle, together with source-bound ledger and stale-test refusal. Real Gemma intent remains UNKNOWN.
9. **Actual edit and independent verification?** Owned CPU edit/tests/submit pass; public Requests CPU transport/edit/submit and actual Native execution are observed. Error-free public Native evaluation is NOT established. No repair success is claimed.
10. **Enter repair-effect experiment?** No. Resolve and revalidate the Requests test-fixture environment before consuming GPU. Do not suppress fixtures, skip failing controls, narrow official scoring or weaken isolation merely to pass this gate.

## Scope and next priority

The previous architecture is one Gemma ADK Agent, six official Workspace Tools plus official SkillToolset, optional executable EGRD Skill, passive research traces and independent Native verification. New V0.2 changes harden its entry instructions, timing accounting and result/cleanup protocol; they do not create a multi-agent architecture or prove improved repair performance.

Next engineering priority is the Native Requests fixture provider/runtime dependency path, and verifying whether its local HTTP fixtures can run within the preserved confinement. Missing providers are observed; a compatible safely isolated service is not yet implemented or verified. Full networking, host mounts and weakened scoring are not acceptable shortcuts. The official file inventory does not contain pytest_httpbin wheels. No substitute task or evaluator is silently used.

After full CPU acceptance, the user's latest '允许CPU和GPU' authorizes the bounded12B smoke. Re-read quota/reservations, validate current source/package/model identities, consume a new one-shot claim and prove exactly four accessible L4 cards before model load. Maximum window18000s with archive/cleanup reserve; Agent300s, command120s,60 tools,80 turns. Retain the original73200s quota admission line. 31B is a separate bounded fallback only for confirmed repeated model-level entry/workflow defects. Both-model entry failure stops experiments.

All300 protected historical file hashes remain unchanged; original S0/R2/EGR/Full, GPU pilot, pilot-frozen and old claims are preserved. Package/source differences from each CPU dispatch are recorded in BUILD_IDENTITIES. Exact task/snapshot, Issue, package/prompt/Skill, model, runtime and evaluator identities are retained. No hidden/reference production answers, official submissions or new GPU inference were used. There is no performance improvement claim.
