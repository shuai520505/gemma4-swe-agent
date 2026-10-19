# Next GPU mechanism pilots — DRAFT, not launch authorization

**This recovery launches zero GPU runs.** The machine draft
`next_experiment_plan.json` fixed task selection before new CPU readiness
outcomes. Final CPU/source/input hashes and environment admissions are attached
in the recovery results; an ineligible task keeps its pilot blocked.

## Independent factors and order

1. Proposed `s1-e3-localize-smoke-03`: `rich_3278`, control → frozen E3.
2. Proposed `s1-e4-contract-smoke-03`: `fastapi_14361`, control → frozen E4.

These are two separate studies. The first proposed GPU authorization is only
the E3 pair, after infrastructure/environment review. E4 is not automatically
launched when E3 ends. No E3+E4 fusion, new Prompt or E1 factor is introduced.
The prior A Patch/trajectory, diagnostic scripts and evaluator artifacts must
not be provided to any new Agent. Neither old stopped experiment is reopened.

Tasks are selected deterministically: within each of Rich/FastAPI, choose the
minimum SHA256 of `s1-infra-recovery-fresh-v1:instance_id` after the conservative
historical/development exclusions recorded in the JSON. Source has not been
optimized against these tasks; their first readiness checks are CPU-only.
Public pretraining exposure cannot be excluded. No outcome-based replacement
is permitted; changing a blocked task requires a separately recorded selection.

## Conditions to freeze before any GPU dispatch

- New experiment ID, remote preregistration commit, exact recovery registration
  source map, latest successful official CPU raw/gate SHA and task environment
  admission SHA. Never substitute CPU source after seeing a GPU outcome.
- Official Gemma 4 31B QAT version 2 and all eight model file hashes from the
  prior actual model identity, rechecked on the future GPU. Same model route,
  4×L4/TP4, context32768, safety1024 and official vLLM parsers/configuration.
- Exact official Wheelhouse map and supplemental dependency map (currently
  none). A task needing unavailable providers cannot pass by using stubs.
- Task ID, declared base, actual snapshot/overlay SHA, full Issue SHA and task
  record hash. Record embedded archive Git HEAD separately. Pin the original
  public baseline readiness test commands/results without leaking them as an
  Agent solution. Hidden evaluation patches remain evaluator-only.
- Frozen control/E3/E4 ZIP and Prompt member hashes, execution order, environment
  adapter/import audit modules, all deadlines and global stop rules.

Both arms of each pair use fresh disposable workers/sandboxes from the same
registered snapshot. Environment and provenance adapters are shared common
infrastructure. Each official Agent remains single, six tools, seed17,
300 seconds, 60 tool calls, 120-second command timeout, output cap16384 and
thinking4096. include_thoughts, temperature/top-p/top-k remain omitted.
Thinking is inside the output cap. Native verification gets 300 seconds;
per-run outer deadline remains 1350 seconds with the unchanged stage caps.
Use setup-origin Notebook clock and 900-second finalization reservation.

No extra model calls, strategy controller or unmetered task-solving checks run
on behalf of either Agent. CPU environment preparation is not an Agent result.
Import observation and evidence I/O consume actual elapsed time identically in
both arms; no budget is extended to compensate.

## Startup and stop policy

Require real model health/models/tokenizer and one actual generation, valid
usage equality and oversize rejection before tasks. Startup costs are separate.
Confirm server-side request reclamation/idle state after a deadline; client
CancelledError and worker cleanup alone do not establish backend completion.
Stop on source/model/parameter/input drift, false environment admission,
reference-data access, unknown request terminal, transport error/timeout,
unverified cleanup, lost native Trace/Patch/Phase2, or inadequate next full slot.

**New cancellation rule:** every dispatched request has a unique ID, exact raw
payload, one matching status event and one terminal. An observed CancelledError
may be explained only with native session-timeout text, elapsed time matching
the registered budget, an Agent-end journal event within ±2 seconds, and
verified sandbox/process cleanup. Do not infer cancellation from a missing
response. Do not retrospectively apply this rule to historical runs.

Explained deadline cancellation does not itself abort a pair if a nonempty
native Patch, real applicable Phase2 outcome and all other infrastructure
evidence are complete. Missing usage remains null/partial and full-token-cost
deltas cannot be asserted. Empty Patch, missing Phase2 or verifier setup errors
produce unknown/blocking outcomes under this pilot, not confirmation of failure.
Ordinary assertion failure with complete valid environment is retained as an
official failure. Native fields remain unchanged in all cases.

Stop immediately if a global gate fails; unstarted runs are not_run. No retry,
task substitution, hotfix or best-of selection within a frozen study.

## Mechanism endpoints and falsification

E3: time to first successful production diff; time/calls before edit; overlapping
or repeated reads; failed tool schemas; diagnostics retained in final Patch;
post-edit verification and explicit submit before cutoff. Earlier incorrect
edits and verification regressions count against E3. A repeated unchanged
search sequence or equally late edit offers no mechanism support.

E4: provenance of post-edit module execution; changed-contract/boundary/old
behavior assertions actually run; invalid/irrelevant tests; verified submission.
Exit0 of an independent hand-coded simulation is insufficient. An unchanged
test sequence with unproven coverage offers no mechanism support. Common
editable/import-audit infrastructure is not attributed to the E4 Prompt.

Both: exact native resolved/Patch/apply/Phase2, raw requests/responses, Token
completeness, tools, elapsed time, finish reasons, context admissions/compactions
and cleanup. Unknown/not_run are excluded from confirmed-failure counts, and
incomplete pairs have no complete repair-rate estimate.

One pair per factor is an engineering/mechanism pilot, not generalization or
leaderboard evidence. Both schedules put control first; warm-cache/order effects
limit interpretation of small timing differences. Any later success-rate study
needs additional fresh tasks and counterbalanced order registered separately.

E1 is deferred to a separate context-pressure cohort, selected using predeclared
baseline admission/slack criteria. This A's input10899/output3230 supplies no
evidence that cap headroom was the binding constraint.

## Cost boundary

Initial future approval should cover only two Agent runs (at most ten Agent
minutes) for E3, plus real startup, setup, verifier and cleanup time. Cold-start
costs from prior GPU logs are material; do not describe Agent-only minutes as
total GPU use. Record actual Notebook/engine/task intervals and distinguish
reservations, device-allocation proxies and unavailable billing. No future
reservation is reported as consumption in this CPU recovery.
