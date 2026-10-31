# R2 raw-trace efficiency audit

Gate and interpretation: this is a read-only analysis of nine historical real Gemma sessions, not a new optimization experiment. All 209 attempted tool actions are classified with raw archive member, line number, call ID and response hash. Analysis starts from raw requests, responses, ADK events, journal and SESSION_RESULT, not previous report totals.

REAL_GPU_OBSERVATION means historical execution. CPU_VERIFIED means analyzer/contract evidence, not new model efficacy. STATIC_ANALYSIS and INFERENCE are labeled. Missing timestamps, official charge boundaries and counterfactual savings remain UNKNOWN/null.

## Time definitions and nine-session reconstruction

T0 is the recorded Agent start. T1 is the first returned source-location/read evidence for the implicated symbol, not an internal comprehension time. T2 internal hypothesis formation is UNKNOWN; the JSON separately records a directly observable causal explanation with event-line/hash provenance. Early xarray/pytest hypotheses can precede source reading because the Issue already contains the stack. That does not mean a safe edit threshold has been met.

T3 is the passive first production-change interval, not a write instant. T5 is the last successful production edit tool call/response bound, not an exact last-write timestamp. Diagnostic-only new files are excluded. T4/T6 distinguish an effective actual-production counterexample/smoke from a passing assertion and from full native resolution. Copied-function toy simulations are not real production validation. T7 explicit diff is distinct from seeing a diff returned by edit_file or internal submit_patch diff collection. T8 retains every submit, including empty and premature submissions. T9 is Agent end, not evaluator/worker/Notebook end.

| # / candidate / task | T1 source proxy | T2 observed hypothesis proxy | T3 production interval | T4 actual-target observation | T5 last edit response | T6 last target/control observation | T7 explicit diff | T8 last submit response | T9 Agent end |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| 1 BASELINE django__django-11964 | 166.716 | 255.224 | Not observed | 92.773 | UNKNOWN / not observed | 220.800 | UNKNOWN / not observed | Not observed | 480.001 |
| 2 R1 django__django-11964 | 15.999 | 68.727 | 214.146–214.371 | 154.052 | 214.374 | 226.072 | 361.115 | 421.447 | 443.103 |
| 3 R2 django__django-11964 | 23.659 | 70.903 | 256.180–256.404 | 315.978 | 399.637 | 412.379 | UNKNOWN / not observed | 422.479 | 435.903 |
| 4 R1 pydata__xarray-6721 | 18.754 | 18.674 | Not observed | UNKNOWN / not observed | UNKNOWN / not observed | UNKNOWN / not observed | UNKNOWN / not observed | Not observed | 480.004 |
| 5 R2 pydata__xarray-6721 | 15.675 | 15.597 | 326.295–326.365 | UNKNOWN / not observed | 326.368 | UNKNOWN / not observed | UNKNOWN / not observed | 433.645 | 448.042 |
| 6 BASELINE pydata__xarray-6721 | 27.367 | 17.239 | Not observed | UNKNOWN / not observed | UNKNOWN / not observed | UNKNOWN / not observed | UNKNOWN / not observed | 433.709 | 446.386 |
| 7 R2 pytest-dev__pytest-5631 | 23.987 | 17.722 | 133.668–133.751 | 171.515 | 133.755 | 171.515 | UNKNOWN / not observed | 264.386 | 277.930 |
| 8 BASELINE pytest-dev__pytest-5631 | 21.282 | 15.254 | 92.374–92.456 | 115.270 | 92.459 | 140.098 | UNKNOWN / not observed | 157.611 | 168.199 |
| 9 R1 pytest-dev__pytest-5631 | 24.569 | 18.393 | 109.138–109.220 | 128.842 | 109.223 | 128.842 | UNKNOWN / not observed | 182.529 | 196.224 |

The JSON retains first/last passing assertions separately. Baseline Django observations expose the bug rather than a repair; pytest in-loop printed helper results are weak observations, not assertion-based native collection passes. R1 xarray and Baseline xarray execute no target tests. R2 xarray has two malformed post-edit probes and no successful in-loop target verification. R12 independent evaluator results remain separate and are not backdated to an Agent test.

## Reconciliation of 1161.87 / 387.3 / 406.9

R2 Agent total = 1161.874847471s; divide by three = 387.291615824s. The generation-scoped coordinator proxy averages 406.924207898s = Agent mean + 19.367476750s worker-import/initialization/sandbox-setup envelope + 0.265115324s cleanup/patch-save envelope before independent verification. The extra mean is about 19.633s, not an extra layer of tool/model waiting.
Import, initialization and sandbox setup are not individually isolated inside that first envelope. Tool execution and model waits already lie within Agent time. submit_patch happens inside it; the small post-Agent envelope includes native save/cleanup, not a second independent submission budget. The proxy starts at the coordinator session admission and stops at the independent-verification stage.

| # | Agent | Pre-Agent import/setup proxy | Post-Agent save/cleanup proxy | Generation proxy | Independent verification excluded | Worker own timer | Coordinator-to-next-boundary wall |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 480.001 | 19.721 | 0.551 | 500.273 | 10.860 | 497.256 | 517.202 |
| 2 | 443.103 | 17.283 | 0.432 | 460.819 | 10.928 | 457.607 | 478.129 |
| 3 | 435.903 | 17.366 | 0.432 | 453.701 | 10.969 | 450.473 | 470.621 |
| 4 | 480.004 | 20.741 | 0.284 | 501.029 | 10.105 | 496.842 | 517.229 |
| 5 | 448.042 | 20.696 | 0.183 | 468.921 | 10.136 | 464.772 | 485.158 |
| 6 | 446.386 | 20.703 | 0.184 | 467.274 | 10.044 | 463.038 | 483.614 |
| 7 | 277.930 | 20.040 | 0.181 | 298.151 | 8.751 | 292.620 | 313.284 |
| 8 | 168.199 | 20.132 | 0.183 | 188.514 | 8.827 | 183.009 | 203.567 |
| 9 | 196.224 | 20.207 | 0.178 | 216.610 | 8.835 | 211.019 | 229.546 |

The R2 worker's own complete timer averages 402.622s; it starts after parent admission/import and includes evaluator work, so it is neither the generation proxy nor total per-session platform cost. Coordinator-to-next-boundary time includes verification/idle/supervision; it is a research wall envelope. Whole Notebook wall time additionally includes shared preparation, model loading, all nine sessions and archive/cleanup. None is a private scorer bill.
**Real official R2 charged time is UNKNOWN.** The 406.924s proxy is the closest observed generation-scope development cost, but is not a measured official cost. Use it only in conditional sensitivity models with explicit official setup/startup uncertainty. 387.292s alone omits preparation; complete worker/Notebook time improperly adds excluded validation. GPU quota-hours are a different accounting unit and are not used here.

## Transport, tools, compaction and tail time

| # | Raw HTTP requests | Native LLM counter | SDK summaries | HTTP union inside Agent | Tool envelope union | Unattributed Agent time |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 29 | 26 | 2 | 466.968 | 10.998 | 2.035 |
| 2 | 31 | 30 | 1 | 429.505 | 12.243 | 1.356 |
| 3 | 23 | 22 | 1 | 423.659 | 11.230 | 1.014 |
| 4 | 29 | 27 | 1 | 476.622 | 2.189 | 1.192 |
| 5 | 31 | 30 | 1 | 438.294 | 8.430 | 1.318 |
| 6 | 35 | 34 | 1 | 442.282 | 2.636 | 1.469 |
| 7 | 22 | 22 | 0 | 270.147 | 6.735 | 1.049 |
| 8 | 13 | 13 | 0 | 160.517 | 6.982 | 0.700 |
| 9 | 13 | 13 | 0 | 189.854 | 5.668 | 0.702 |

R2 total transport union is 1132.100s (97.44% of Agent time); tool envelopes total 26.394s (2.27%). These intervals were clipped to Agent start/end, unioned and checked for overlap. Request/terminal pairing covers all nine. HTTP includes queueing, model prefill/decode and transport; pure generation, queue-only time and internal thinking time are UNKNOWN. Tool envelopes include host dispatch; exact sandbox-only duration is UNKNOWN. Gaps are not labeled thinking or waste.
The raw count is 226 requests versus 217 in the native LLM counters. Seven no-tool requests explicitly ask the SDK to summarize the conversation; two final interrupted requests have no completed model event. R2 has two SDK summaries totaling about 40.339s. These requests consume real loop time and are included in transport/token observations. The compaction setting remains frozen; there is no third candidate tuning it.

Post-submit tails are measured in the JSON. The official loop waits for a final text completion after submission and may allow further tools before that completion. In R2, the tails contain real final-completion HTTP, not a demonstrated idle wait. Final invalid waiting time therefore remains UNKNOWN; do not subtract the whole tail as a guaranteed saving.

## Tool-level cost and information audit

R2_TOOL_ACTION_AUDIT.json classifies each of 209 actions into the requested 12 categories, preserving 192 charged calls separately. Each action has its next action ID and an observed-transition assessment. A path returned and read next is observable information use; whether it caused an internal model decision is not identifiable. Same-source rereads, negative greps and failed assertions are not blanket waste labels. A reread after context compaction may refresh information even if no new source bytes appear.

| # | Charged/attempted | Effective reads | Invalid reads | Effective edits | Parameter edits | Repeated edits | Useful tests | Invalid tests | Env | Diff | Status | Submit | Other |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 22/26 | 12 | 4 | 0 | 4 | 0 | 2 | 0 | 4 | 0 | 0 | 0 | 0 |
| 2 | 26/29 | 9 | 0 | 1 | 0 | 0 | 7 | 2 | 2 | 3 | 1 | 2 | 2 |
| 3 | 20/21 | 5 | 0 | 1 | 0 | 2 | 9 | 3 | 0 | 0 | 0 | 1 | 0 |
| 4 | 27/27 | 27 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 5 | 28/29 | 24 | 1 | 1 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 1 | 0 |
| 6 | 28/33 | 26 | 2 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 2 |
| 7 | 19/20 | 6 | 2 | 1 | 0 | 0 | 4 | 1 | 0 | 0 | 0 | 1 | 5 |
| 8 | 11/12 | 3 | 1 | 1 | 0 | 0 | 6 | 0 | 0 | 0 | 0 | 1 | 0 |
| 9 | 11/12 | 4 | 1 | 1 | 0 | 0 | 4 | 1 | 0 | 0 | 0 | 1 | 0 |

Expected pre-fix NumPy ValueErrors and R1 Django failing reproduction assertions are useful tests, not malformed-tool failures. An invalid test here means a broken fixture, copied test not exercising the production change, or environmental setup preventing the intended check. Useful tests have a scope tag; a toy mechanism check is not a production success. A printed passing-looking message is weaker than assertions.

The five BASELINE malformed edits omit old_string while the actual request schema requires it. Their JSON parses and finish reasons are retained, so this is not merely a truncated display or an absent schema. Four consecutive Django attempts repeat this defect; xarray makes one and later two schema-valid edits are budget-rejected. Parameter-rejection envelopes sum to about 0.056s; the five eliciting HTTP rounds sum to about 69.023s. That is exposure, not proven removable cost. R1/R2 made zero such calls. R1 explicitly asks for full required arguments; R2 does not add that recovery instruction and takes a simpler different edit path. The data cannot identify whether prompt content, chosen patch, context or sampling caused the zero error counts.

## Per-session evidence review

1. BASELINE Django: three initial fixture setup failures, then an actual fresh-vs-readback counterexample at 92.773s. It explores descriptor/field conversion and never edits production. Four late malformed edits cannot execute; only diagnostic temp_app files remain. Wrong-path lookups and invoking read_file as a shell command add avoidable recovery work. Reading field/descriptor code may be a legitimate alternative hypothesis, not retrospectively all waste.
2. R1 Django: source-backed Enum hypothesis and a legitimate failing reproduction precede the edit. Actual reproduction passes at 226.072s. A broader test command fails on setup, and compatibility/serializer reads can add information. First submit is 2496 bytes/two files; diagnostic removal produces a genuinely different 390-byte one-file final submit. Those corrective diff/submit actions are necessary given the first submission, not a no-op loop.
3. R2 Django: a concrete Enum hypothesis is visible at 70.903s but not independently proven there. A smaller actual edit occurs at 256.4s; direct string assertions pass at 315.978s. MRO/type checks add compatibility information. A late revert/counterfactual/restore cycle invalidates the first passing version and requires revalidation at 412.379s. The repeated final test is necessary once that production reversal exists; the whole reversal is the research opportunity, not deleting revalidation alone.
4. R1 xarray: repeated source-path reasoning consumes the deadline with 27 charged calls, no production edit or test. Some late reads revisit an unchanged helper already seen; they provide no new source bytes, but compaction/decision refresh prevents a universal zero-value claim. A plausible hypothesis stated from the Issue is not proof of edit readiness.
5. R2 xarray: the cause is hypothesized early, but 20 source/navigation operations precede the edit at 326.36s. An out-of-bounds read is a real tool misuse. Both later fake-array tests fail because their fixture does not preserve the intended lazy interface. Submission is valid by later independent evaluation, not because these probes passed. Caller/duck-array/chunk metadata checks have genuine regression relevance and cannot all be removed.
6. BASELINE xarray: source exploration continues into other .data.chunks sites; one late edit omits old_string and two later edits exhaust the tool budget. Two submits both return zero bytes/files. get_status/submit being uncharged does not make an empty patch a repair. Negative searches can constrain hypotheses, while the late wrong source window and repeated empty submit add no repair evidence.
7. R2 pytest: two writes overwrite repro.py before its first run; copied original/fixed microcases establish the equality mechanism. Production edit at 133.75s is later than BASELINE. Rerunning copied old logic after the edit does not test the actual patch. A real helper smoke prints expected values at 171.515s but lacks assertions, and the compat suite yields six passes/two fixture errors. Necessary diagnostic cleanup precedes a clean first submit. Later negative searches differ and may inform coverage; not every grep is waste.
8. BASELINE pytest: membership counterexample plus identity/default microcases precede the earliest production edit (92.46s). Three actual helper smoke outputs cover array/default/attribute_name. These are useful controls even without a native collection assertion. A targeted source grep exposes the changed line before submit; absence of an explicit git diff is not absence of all source inspection.
9. R1 pytest: a wrong patch.DEFAULT microcase fails, corrected reproduction then exposes the real array error. A combined actual-helper check covers four cases. One extra focused read/grep can verify code rather than constitute broad exploration. It edits later than BASELINE but earlier than R2.

## Ranked bottlenecks and optimization limits

1. Decision latency after a source-testable hypothesis: R2 first changes are 256.4/326.4/133.8s. Observable hypothesis-to-edit windows are not removable-time estimates; they contain necessary source/compatibility work. R1 xarray shows the failure mode of never converting inspection into a production attempt. Candidate A is the most direct single-factor hypothesis, with correctness risk explicitly guarded by a discriminating evidence threshold.
2. Diagnostic/verification construction and binding: R2 has six invalid-test attempts (three Django, two xarray, one pytest). Their tool envelopes total about 8.791s and associated HTTP rounds about 122.950s; expected bug failures are excluded. The copied old pytest repro is additionally misbound to the real edit. Replace a broken probe with a valid actual-path check, rather than remove required verification.
3. Recovery/finalization rework: schema-rejected edits are failure-associated in BASELINE, while R2 already avoids them. R2 Django has a deliberate source reversal; R1 Django shows the need to remove diagnostics before the first submission. Candidate B is a secondary version-bound closure hypothesis. No safe quantitative saving is established by merely deleting these observed operations.
See BOTTLENECK_EVIDENCE.json for counts, raw call IDs and separately measured envelopes/eliciting-HTTP costs. These groups overlap phase windows and are not summed into fictitious total savings. R2 alone has no post-submit tool loop or empty submission; older Action-First observations are corroboration, not a pooled effect estimate.

## Action-First corroboration

The original GPU03 archive was CRC/SHA checked and all four model tool trajectories read. One A case has no production edit and context-guard rejection; another has the same rejection but a valid retained patch. In fastapi_14786-A, an initial successful one-file 404-byte submit is followed by two git diff calls, a second same-size submit and git status. Same arguments/results are documented. Broader pytest encounters missing multipart dependencies; later focused checks supply real evidence. The study used different budgets/context guards and two already-seen FastAPI tasks, so it is neither new held-out evidence nor a transferable success-rate/time model.

## What can and cannot be removed

Structurally avoidable: missing required parameters, invalid source ranges, unexecuted diagnostic overwrites, rerunning a copied old function as if it tested changed production, and truly identical repeated submission of an unchanged verified patch. Removing these failure modes may still require a replacement valid check or edit; net savings are UNKNOWN.
Do not remove the first discriminating counterexample, target assertions, required positive controls, compatibility checks that reveal new constraints, test-input/environment disambiguation, cleanup needed to keep a production-only diff, or revalidation after any real source/test-input change. No additional status or explicit diff call is assumed free in wall time: uncharged tools still induce model/host work.
