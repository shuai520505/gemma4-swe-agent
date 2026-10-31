# R2 behavior audit

REAL_GPU_OBSERVATION: all nine complete ADK tool trajectories were parsed, paired by tool-call ID, and aligned to each recorded agent_started monotonic time. Full call arguments, responses, errors, commands, repeats, status calls and submission timing are retained in R2_BEHAVIOR_METRICS.json. These timestamps observe event delivery, not an exact internal model decision or filesystem write instant.

| R2 task | get_status | First production change interval | Last successful production edit response | Strict successful target test | submit_patch call | Time left at submit call |
|---|---:|---:|---:|---|---:|---:|
| Django | 0 | 256.18–256.40s | 399.64s | First 315.98s; last 412.38s, Text/Integer assertions | 421.97s | 58.03s |
| xarray | 0 | 326.30–326.36s | 326.37s | None: both custom probes failed | 433.49s | 46.51s |
| pytest | 0 | 133.67–133.75s | 133.75s | None meeting strict assertion criterion; real-function smoke printed expected 0/1 at 171.52s | 264.20s | 215.80s |

First localization is not directly observable. The JSON reports first relevant source read as a proxy and keeps exact understanding time UNKNOWN. The passive observer only persisted the first production change; last successful edit response is an observable bound, not a fabricated exact last-write time. No new GPU inference was used for this analysis.

## Six frozen rules against observed actions

| Rule | Finding | Assessment |
|---|---|---|
| Make a minimal production change early | Minimal final diffs, but Django first changes after 256s, xarray after 326s of 480s. pytest is later than Baseline (133.7s vs 92.4s). | Partial; no uniform early-edit improvement |
| Check get_status after localization/edit and before long operations | Zero get_status calls in all three R2 sessions. R1 Django alone calls it once among all nine. | Not followed |
| Budget from remaining time/calls and reserve focused verification/diff/submit | Automatic tool responses warn about remaining calls. Submission retains about 58/47/216s, but no direct status observation; xarray consumes all 28 charged calls. | Delivery reserve observed; actual time-driven adaptation unproven |
| Stop broad/optional investigation near deadline | Django reverts and restores its correct edit late; xarray continues reading and custom-probe design with only a few calls left. | Partial/weak compliance |
| Bound checks by remaining time after finalization reserve | No explicit dynamic timeout calculation or get_status evidence. xarray has no successful in-loop target check; pytest's suite command has fixture errors. | Not demonstrated |
| Inspect diff and submit a valid production fix | All three explicitly submit nonempty, subsequently validated patches. No explicit git diff command in any R2 trajectory. submit_patch internally collecting a diff is not the requested pre-submit diff review. | Submission followed; diff-review action not followed |

## Failure and repetition review

R2 made zero missing-required-parameter edit calls. This is narrower than zero tool failures: Django had three command errors, xarray three and pytest five. The JSON retains each exact error. Syntax, model app_label and synthetic-array construction errors were model-generated diagnostic mistakes, not evidence that the real production patch failed.

Django's initial standalone Enum demonstrations are not tests of production Django. Its first real production assertions pass after the edit. It then removes the fix, checks old output, restores it, and reruns assertions. This counterfactual has diagnostic value, but adds late work after a valid patch already exists. Its database test failed on missing app_label, so in-loop database consistency was not demonstrated; the independent evaluator and expanded CPU audit supplied that evidence separately.

xarray's two post-edit diagnostic programs both fail due to the synthetic object's construction/metadata assumptions. They cannot be counted as successful verification. Its final patch is supported by the independent actual Zarr counter test, not by those failed in-loop experiments.

pytest writes repro.py twice before execution, later reruns its copied old implementation after the production edit, and performs several unsuccessful greps. The production-function smoke prints the expected results, but catches an error and lacks assertions; it is weak evidence. The existing test_compat command reports six passes and two setup errors, not a passing suite. The original Issue native collection check passes in the independent evaluation. The current CPU audit adds assertion-based collection controls separately.

## Comparison and interpretation

Baseline never edited production on Django/xarray; R2 did and explicitly delivered both. All three candidates fix pytest, where Baseline modifies production roughly 41s earlier than R2 and finishes its Agent loop roughly 110s earlier. R2 therefore shows better edit/delivery coverage, not universal speedup.

INFERENCE: having a real production edit and a nonempty submission directly supplies necessary repair artifacts. The trace cannot identify whether the appended R2 rules caused this; no independent repetitions or new held-out tasks exist. The three development fixes are small and the inherited Baseline already has a strong call plan. Task simplicity, stochastic variation and order/model warm-up remain alternative explanations. A 3/3 outcome does not establish obedience to the status-check rules or hidden-task generalization.

No R1/R2 merge or R3 was created. R2's exact prompt remains frozen. A separate budget experiment should measure actual adherence and validated repairs per globally charged second, rather than add more wording based only on this pilot.
