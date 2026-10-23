# Observed failure mechanisms and evidence limits

Twelve actual GPU sessions (PR24, PR27 Batch1, PR28) were re-read from the three pinned private ZIPs listed in `TRACE_BEHAVIOR_METRICS.json`; archive SHA and CRC checked. The analysis uses all315 actual ADK tool calls, paired responses, HTTP usage and post-Agent-start production hash observations. Raw arguments/responses and model reasoning remain outside Git under `private-evidence/u_re_v04_trace_audit/`. No reference/gold patch was fetched or read.

## Operational evidence hierarchy

A relevant path or function read is a source observation, not a localized defect. An explicit falsifiable hypothesis is a candidate explanation, not a verified repair. An observed target failure is stronger; actual production mutation is still only a repair candidate. A relevant post-edit assertion/regression pass gives local support. Same discriminating test failing before and passing after is stronger still. Final original Native TaskResult/JUnit determines resolved. Explicit submit is an independent lifecycle event.

Automatic classifications A-M are conservative: A and D concern interpretation/intent and are not assigned from a tool name. Hypothesis-first times and genuinely discriminating pre/post-test times stay null where not established. Operation-end edit times are upper bounds, not exact write-syscall timestamps. Category J means behavioral candidate, never automatically correct. Category I includes useful supporting imports as well as diagnostics. Test-path/dependency H is an additional tag, not lost when a failed command is also E/G/K.

## Measured diagnostic cost

Times are seconds since actual Agent start; - means null. New reads count previously unseen successful target implementation read responses, including different file windows, not proven causal information gain. Received Token totals are cumulative actual usage and can count repeated history; they are not new semantic content. All per-action indices, hashes and categories are in the JSON.

| Cohort / run | First implementation read | First production edit | First behavioral candidate | Tools before edit | Received tokens before edit | Novel reads | Path / dependency errors | Native resolved |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| GPU03 / 01-fastapi_9425-A | 25.267 | - | - | - | - | 4 | 0 / 0 | False |
| GPU03 / 02-fastapi_9425-B | 28.249 | 138.953 | 138.953 | 22 | 164867 | 6 | 0 / 0 | True |
| GPU03 / 03-fastapi_14786-B | 7.307 | 30.341 | 30.341 | 5 | 16939 | 2 | 1 / 1 | True |
| GPU03 / 04-fastapi_14786-A | 7.525 | 29.648 | 29.648 | 5 | 15854 | 2 | 0 / 1 | True |
| V02B_BATCH1 / 01-fastapi_5077-A | 13.898 | - | - | - | - | 4 | 1 / 1 | False |
| V02B_BATCH1 / 02-fastapi_5077-B | 9.929 | 153.133 | - | 17 | 167009 | 3 | 1 / 0 | False |
| V02B_BATCH1 / 03-fastapi_11355-B | 99.222 | - | - | - | - | 5 | 0 / 0 | False |
| V02B_BATCH1 / 04-fastapi_11355-A | 19.118 | 135.377 | 135.377 | 22 | 187584 | 7 | 1 / 0 | False |
| V03 / 01-fastapi_5077-A | 17.039 | 149.530 | 149.530 | 19 | 149384 | 7 | 1 / 0 | True |
| V03 / 02-fastapi_5077-B | 10.621 | 182.513 | 182.513 | 15 | 112762 | 2 | 1 / 1 | True |
| V03 / 03-fastapi_11355-B | 43.078 | 274.974 | 288.080 | 38 | 407133 | 7 | 0 / 0 | False |
| V03 / 04-fastapi_11355-A | 70.124 | - | - | - | - | 5 | 1 / 0 | False |

Across315 actions,54 successful source reads provided a distinct observed source response. This is a lower-level novelty count, not an estimate that only54 actions were useful.113 localization actions and60 implementation reads cannot all be dismissed as waste. Three exact repeated searches with unchanged query/result/production epoch and two unscoped pytest invocations are directly identifiable. Necessity/information gain of every other diagnostic is UNKNOWN. Negative searches and a first failed path probe can be legitimate evidence.

## A. Search and delayed repair

V03 `03-fastapi_11355-B` (8192) read implementation by43.078s, then continued searches, signature/caller inspection and several reproduction scripts. The same absent-symbol query occurs at ADK tool-event indices18 (36.819s) and70 (233.719s), with unchanged production state and identical negative result. A later HTTP response35 at233.702s contains a concrete candidate hypothesis; response36 at274.791s contains a local repair plan. These are observed late hypotheses, not a claimed earliest hypothesis timestamp. Speculation in the model text about another project's implementation was not verified or used as external repair evidence.

The first production change at274.974s is only a supporting import; the first behavioral candidate is288.080s, and another mutation occurs near298.7s. The300s deadline leaves no observed post-edit assertion run. Native result is false.407,133 received Tokens were consumed before the first production edit. Extra context allowed continued diagnostics, not demonstrated earlier effective repair. This sequence supports a missing evidence-to-action decision and a weakly tested reproduction/hypothesis, not proof that a correct edit was already obvious at43s or that a particular earlier edit would succeed.

GPU03 `01-fastapi_9425-A` spent264.284s/179,265 received Tokens,26 tool actions and4 novel implementation reads without an actual production edit; context guard stopped it. PR27 `01-fastapi_5077-A` similarly had22 actions/219,622 Tokens and no production change. This establishes diagnosis-without-production-repair in those sessions; it does not establish all exploration was unnecessary. Missing first-edit metrics stay null, with whole-session cost reported separately in JSON.

## B. Reproduction and weak local evidence

PR27 `02-fastapi_5077-B` has a production hash change at153.133s that only adds diagnostic output, not a target behavioral repair. Its self-created pytest test body has no operative assertion (`pass`); a green result therefore does not distinguish repaired behavior. Print/catch-based scripts in V03 also cannot establish correctness merely by exiting0. The EGR block consequently asks for observable assertions, exceptions that fail honestly, and correction of a misdirected reproduction instead of proliferating similar scripts. No hidden assertion is included in the candidate.

## C. Test-selection errors versus trustworthy evaluation

V03 `02-fastapi_5077-B` first changes behavior at182.513s. It invokes unscoped pytest, collecting702 items and162 collection errors, including an optional-dependency failure, and later requests a nonexistent test directory. It then runs relevant existing tests (4+1 pass), explicitly submits near253.112s and finishes near259.806s. This shows avoidable test-scope/path selection cost and a poor separation of optional full-suite environment issues from target validation. Existing regression passes are local support, not a demonstrated same-test fail-before/pass-after proof. The trusted native verifier independently resolves the task with0 errors. No test was deleted or dependency added to hide this Agent-side result.

The new policy checks path/relevance before invoking a test and expands scope only for a specific regression concern. It does not forbid broad tests when justified, suppress failures, or insist every edit must wait for a successful reproduction.

## D. Correctness, submission and termination are separate

V03 `01-fastapi_5077-A` forms a behavioral candidate at149.530s, is stopped by the context guard around164.45s without explicit submit, and its exported patch later resolves under the native verifier. A correct final patch can therefore coexist with a guard stop and no explicit submit. GPU03 `04-fastapi_14786-A` explicitly submits twice and performs four tools after the first successful submit; Action-First closes promptly in its corresponding successful sessions. These are observed lifecycle differences, not proof an instruction change alone guarantees termination.

Historical changes to allowed workspace tests are not automatically counted as production fixes or accepted as a way to change the trusted evaluator. The V0.4 instruction retains the original prohibition on modifying evaluator tests. Native tests/Verifier and all historical patches/results remain unchanged.

## What can and cannot be addressed with one instruction factor

Plausible instruction targets: explicit contract/hypothesis, purposeful diagnostics, correction of uninformative reproductions, evidence-sufficient minimal behavioral changes, targeted assertions/path checks and timely closure. These are hypotheses for future real Gemma tests. The candidate does not impose edit quotas, fixed submission seconds, hidden-test guidance, extra agents, or runtime tool rewriting.

Kernel capabilities, actual dependency availability, hard context/output/time/tool limits, backend errors, reliable token accounting and enforceable post-submit termination need engineering or separate experimental factors. They are not silently changed here. More input capacity alone did not improve V03 native outcomes, but this does not prove the32768 context or16384 output cap is optimal.

## Isolation and development bias

The inspected tasks are development/mechanism samples. They are excluded from prospective confirmation. Only generic decision principles, not evaluator contents, old patches, task-specific APIs, model trajectories or proposed task solutions, enter EGR. Original Action-First/NoEGV/Full ZIPs are unchanged. Public derived evidence consists of counts, times, hashes and conservative annotations; raw traces/patches/evaluator content stay private.

The V04 candidate is untested algorithmically. Scripted CPU success proves the execution path and actual Prompt wiring, not improved decisions or repair rate.
