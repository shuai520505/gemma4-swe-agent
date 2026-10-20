# CPU feedback-loop acceptance

CPU02:135/135 passed in one complete preparation:115 original research regressions +7 frozen T500 methods +8 new workflow methods +3 authorization/window guards +2 exact-budget methods. The eight new methods include controlled subcases; do not count subcases/tool calls as independent GPU tasks. Logs and full real events are under results/cpu02/validation. Model replies are scripted HTTP; source edits, assertions, ADK AgentTool dispatch, returned tool evidence and submit are real.

| Test | Actual path and result |
|---|---|
|A| Before any production edit, Main delegates a specified failure question. Child reads unchanged app.py and executes failing checks.py; FAIL evidence returns and is stored in egv_latest_report. No repair/loop is claimed for this delivery-only case. |
|B| Pre-Patch child failure -> Main changes False to n>=0 -> actual target and negative-regression assertions pass -> git diff check -> submit,155-byte intended-source Patch.6 charged tools,10 raw tool events,12 model requests (Main8/child4). |
|C| Main makes n>0 Patch -> child fails target -> report returns -> Main changes to n>=0 -> child target/old-negative passes -> diff -> submit.8 charged tools,13 raw events,16 requests (Main9/child7). |
|D| Actual get_status reports~29.88s remaining after a test clock offset; direct check/diff/submit without EGV. This is simulated late-time control flow, not an actual470s wait. |
|E| Real scratch_probe.py creation/deletion; final submitted Patch contains only app.py, not scratch. Pre-existing checks.py preserved. |
|F| Four actually executed controlled probes distinguish wrong expectation, production behavior failure, missing probe dependency and unverified exit0 using the immutable fixture contract and canonical assertions; no generic exit-code production verdict. |
|G| Real nested request cancellation propagates; absent usage remains null/partial; intentional child Shell write is detected by source hashes. Detection is not enforced read-only isolation. |
|H| Simple direct repair/check/diff/submit works with no EGV. This reuses the same near-deadline direct sequence as D, not an independent timing-policy efficacy experiment. |

For B, immutable nested_audit.jsonl tool-end lines23(child failing command),26(report delivered),30(Main edit),34(target+old-behavior successful retest),42(submit). For C:27,30,34,45(successful child retest),48(PASS delivery),56(submit). All refer to early_cases/B_early_repair or C_post_patch under the CPU02 validation folder. Tests do not infer execution from report words: they join actual failing command evidence, delivery, successful source mutation and later successful assertions.

The original n>0 -> n>=0 toy is synthetic, not a public-task repair answer. No public-task model run or leaderboard success is claimed. CPU01 passed the Compiler,115+7 originals and7of8 new methods but errored in Test A's event-kind audit; original raw error/source/Trace preserved. CPU02 reruns everything and is the sole acceptance basis, not a composite.

Actual new-candidate500s cancellation: native agent elapsed500.100011418s; child request cancelled, native timeout reported, usage null, before/after workspace hashes stable before sandbox stop, cleanup complete.60-count test records exactly60 charged calls but71 raw events (free operations and denied attempts are distinct); free submit succeeds without claiming the deliberately under-repaired Patch was correct. See early_exact_cases and early_exact_budget.log.

Real tokenizer on the pinned31B model files:853 ->1208 standalone Main instruction tokens, +355. This measures text length, not real inference latency, full templated request consumption or algorithm benefit.50 uncached repetitions would add17750 input tokens as a scenario; actual caching, compaction, roles and call count determine cost.
