# Next minimal experiment — preregistration design, not authorization

Status: DESIGN_ONLY_NOT_DISPATCH_READY. No task is selected, no new Agent package is built, and no GPU/SaveKernel/inference/submission occurs in this audit. A separate authorization and a frozen, reviewed execution manifest are required. This protocol is single-factor falsifiable even though actual task IDs remain pending prospective selection.

## Question and single factor

Compare frozen R2 control with Candidate A only. Change exactly one inherited CALL PLAN edit-decision bullet as described in R2_OPTIMIZATION_HYPOTHESES.md. Preserve the exact six-rule R2 suffix, the rest of the system prompt, issue text, model identity, nine tool registrations/schemas, inference API, temperature=.2, top_p=.95, max_output_tokens=8192, thinking_budget=4096/include_thoughts=true, prefix-cache policy=false, LoRA=false, tensor parallelism and context/compaction settings. Keep 480s Agent, 28 charged calls, 80 turns and 240s commands in both arms. Do not introduce a per-arm timeout change, R1 recovery text, extra graph tool, seed configuration or stop-controller as another factor.

The future exact prompt diff must contain only that one bullet replacement. Compile both with the frozen official SDK and compare all non-prompt members plus parsed tool schemas/generation/budgets before any inference. There is no candidate ZIP in this design directory. Candidate B is not part of this experiment and needs a separate protocol/holdout if tested later.

## Prospective independent holdout and order

Minimal pilot: four genuinely new public-development tasks, from four repositories or the widest available repository blocks, one paired control/treatment session per task: eight real sessions total. Exclude every task/Issue/base snapshot used to design A, including all three R12 tasks and both Action-First FastAPI tasks, and previously inspected/screened cohorts. Use an auditable exclusion list from project exposure history before selection. Do not call a task independent just because its ID differs if the same Issue/base commit was already used.

Before candidate outputs are seen, freeze the eligible four-field Issue cohort (ID/repo/base_commit/problem_statement), snapshots/dependencies, native evaluator specifications and hashes; no reference repair is shown to the Agent or analyst. Select by a seeded metadata-only rule across repository/Issue-type blocks, not expected ease or observed repair performance. The published native validation tests may be loaded only by the trusted official evaluator, not used as prompt/solution hints. No hidden tasks or gold repair patch is used.

Use two AB and two BA task pairs, with a preregistered ordering seed that only randomizes run order; no new model-request seed is added to the frozen sampling config. Interleave pairs across blocks so treatment is not confounded with all cold/warm sessions. Each run gets a fresh workspace, model context, snapshot and independent evaluator; no conversation, patch or diagnostic transfer. One run per pair is a pilot, not a reliable estimate of per-task stochastic variance.

## Official endpoint and trustworthy measurements

Primary: actual official SDK TaskResult.resolved with trusted native verifier/JUnit artifacts, accompanied by independent semantic approval of effective production changes and necessary controls. If the native verifier/fixture cannot be validated, mark NATIVE_ENDPOINT_UNAVAILABLE and stop; do not substitute owned synthetic pass counts and call them Native Resolved. Keep canonical SWE-bench resolution separate unless actually run. CPU scripted contract tests validate plumbing only.

Reuse the existing Runner/Worker/Coordinator, official tool registry, independent evaluator, HTTP observer and cleanup mechanism. Prospective measurement must passively record before/after production AND test-input/environment identity for mutating operations and actual command results, including run_command. This identical observer belongs outside both Agent decision/tool-return paths; CPU-validate its import/overhead/identity handling before dispatch. No official SDK source, test expectation or per-arm behavior may be patched to create a favorable result. It is a prerequisite proposal, not newly implemented controller code.

Log Agent start/end, preparation, patch-save and verifier boundaries separately; raw request/terminal pairs, compaction requests and full available usage; all tool call/response IDs; first production-change intervals; final production diff; every explicit/fallback patch; cleanup receipts and platform status. Store missing data as UNKNOWN, never zero.

| Metric | Definition / limit |
|---|---|
| Native Resolved | Official native result, not owned development endpoint or tool status |
| Validated Repair | Native/target checks plus controls, real production fix and separate semantic review |
| First Production Edit | First observed changed tracked production bytes, with timing interval |
| Time to Validated Repair | Actual run-start to first independent validation completion; do not backdate to first edit. Keep generation-only cost separate. |
| Successful Submit Rate | Explicit nonempty production submit whose final patch is validated; empty/mixed-scope first submissions separate |
| Invalid Tool Rate | Preregister schema/malformed/budget-rejected operations and denominator; expected bug assertion failures are not invalid calls |
| Tokens per Resolved | All arms' observed tokens including failed sessions/SDK summaries divided by validated repairs; UNKNOWN if incomplete or zero repairs |
| Wall-clock per Resolved | Full measured wall and generation-scope proxy reported separately; verification is excluded only from the official-budget denominator |

For intermediate correctness timing, require a native-independent evaluation checkpoint tied to actual source/test identity before claiming an earlier validated repair. Otherwise only final correctness and observable first-edit are known. A later passing final patch cannot certify an earlier transient version.

## Resource bound and stop rules

The platform window, quota accounting and capacity must be re-read at a later authorized execution; no resources are checked/allocated here. A prospective five-hour pilot envelope could reserve at most 1500s bootstrap, 2400s preparation, 1300s model stage, 8*1200s complete-session admission (including independent verification), and 900s final archive/cleanup: 15700s total, with 2300s uncommitted margin under an assumed 18000s window. These are admission caps, not expected costs or a newly granted window. If the actual trusted native setup does not fit, block before dispatch and obtain a separately reviewed plan; do not silently reduce Agent budget or skip checks.

Keep ordinary repair failures and follow the frozen order, with no selective retry. Stop subsequent admission on model/context/backend incompatibility, dependency/positive-control/isolation/evidence/cleanup failure. Mark untouched suffix NOT_RUN and invalidate any claim of complete-batch improvement; do not coerce infrastructure missingness to repair zeros or rerun until a favorable result appears. Predefine how complete/broken batches are reported before launch.

## Analysis and falsification

Compare paired native/validated outcomes, retaining all failed-session costs. The four tasks are the inference units; tool calls/tokens are not independent samples. Report both-win, only-control, only-treatment and neither, plus each task's time/cost and every failure. Use paired cost differences/ratios and explicit small-sample uncertainty; four tasks cannot establish non-inferiority, a tail distribution or leaderboard 0.50.

Pilot advancement requires no observed correctness loss, no new wrong/test-only/diagnostic-only patch pattern, no trust failures, and a meaningful improvement in generation cost per validated repair. The N=120/10% case motivates a 25% cost-reduction research target, not a fitted expected effect or a pass criterion achieved by deleting checks. Faster first edits, fewer tools, a shorter prompt or a lower mean among successes alone do not qualify. Faster but less correct, more errors, unchanged effective repair yield with only call-count savings, or higher cost without repair benefit rejects advancement.

Any pilot signal must be confirmed on a larger untouched cohort with a separately preregistered sample-size/precision and full global-budget accounting. Do not select between A/B on the same four outcomes or rebuild R3 from a favorable subset. No formal competition score is claimed until a later explicitly authorized submission obtains one.
