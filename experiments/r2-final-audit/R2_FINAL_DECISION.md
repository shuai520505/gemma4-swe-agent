# R2 final decision

**R2_BLOCKED_BY_BUDGET**

R2 is worth preserving as the next formal-candidate basis. It is not recommended for immediate unchanged full-workload submission. The exact frozen ZIP passes a new real CPU official Compiler run and remains byte-identical to the tested R2. Its only package difference from the historical 0.15 Baseline is the appended R2 system prompt. The old repository submission directory is not the scored Baseline and was not overwritten.

| Review gate | Result |
|---|---|
| R2 prompt/includes and root packaging | CPU_VERIFIED PASS |
| Baseline/S0/R1/R2/history preservation | Hash verification PASS |
| Single strategy difference vs scored Baseline | ZIP member comparison PASS |
| Actual frozen official Compiler | CPU_VERIFIED PASS |
| Three patch reviews | Completed; expanded checks pass, original Django suite has two shared Python compatibility errors |
| Django label explained | Exact generator and same-base contrast verified |
| Official 12-hour model and scenarios | Completed, but safe full workload coverage is not demonstrated |
| eval_config meaning/support | Four R2 keys verified; old verification override is local-only |
| Unknowns explicit | Listed below |
| Final ZIP SHA256 | `af918c1a65aeb211298f13a69b5b789ae6b086974922c80469df87d902eb98d5` |

R2's three development successes remain 3/3 in owned Issue-grounded evaluation, not official Native Resolved or canonical SWE-bench. The focused CPU audit supports patch semantics; it does not establish hidden-task success probability. get_status was called zero times by R2, and all three lack explicit git diff; full compliance with its six rules is not demonstrated. pytest's first production edit and total Agent time are worse than Baseline. Do not attribute the pilot difference causally to the Prompt.

The R12 R2 Agent mean is 387.29s; measured setup/save-inclusive generation proxy is 406.92s. With assumed N=120, setup/model allowance 1500s and 10% reserve, the safe task average is 311.5s. Conditional mean-profile capacity is 91 tasks; the corresponding mean cost reduction required is about 23.5%. Exact N remains OFFICIAL_TASK_COUNT_UNKNOWN; organizer materials describe approximately 120, not a guaranteed 60-task workload. The current eight-minute cap plus setup cannot guarantee all-task coverage. This budget block expresses insufficient safe-execution evidence, not a proven measured private-scorer timeout.

Next priorities toward 0.50: establish scorer timing/override boundaries and task-count assumptions; design a separate budget-only or explicitly prompt-consistent budget experiment; measure tail costs and early-stop behavior on a pre-frozen holdout with paired runs; count all failures and protect independent semantic/regression checks. Compare validated repairs per global generation second, not just per attempted task. Obtain official feedback only after a later explicit submission authorization. R3 is neither necessary for this audit nor created here.

Unknown / NOT_RUN items:
- OFFICIAL_TASK_COUNT_UNKNOWN: approximate organizer description about 120 is not exact N
- Private scorer global timer implementation, task order, overrides and model startup charging boundary
- Official scorer runtime/caching equivalence to R12 custom sandbox and server
- Local CPU SDK metadata dependency closure is incomplete for model-serving-only modules; see SDK_DEPENDENCY_CHECK.txt. Actual compiler/tool registration passed without stubs. Full host serving validation: NOT_RUN this audit.
- Complete historical Django functional API on a compatible pre-3.11 Python runtime: NOT_RUN; both baseline and R2 error under current Python 3.12
- Full framework regression suites: NOT_RUN
- Official Native Resolved and canonical SWE-bench Resolved: UNKNOWN/not measured
- Hidden-task repair probability and tail-cost distribution: UNKNOWN
- A deployable organizer-supported global-budget callback: not verified

No GPU Notebook, SaveKernel, model inference, competition submission, model switch, selective R12 rerun or frozen-candidate mutation occurred in this audit. The required package is delivered for inspection only. This final gate does not authorize submission.
