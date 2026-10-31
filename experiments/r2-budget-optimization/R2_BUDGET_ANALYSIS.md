# Shared 12-hour budget model, corrected scopes

OFFICIAL_RULE: the [competition overview](https://www.kaggle.com/competitions/gemma-4-developer-agent/overview) gives one all-task patch-generation limit of 43200 seconds, includes sandbox preparation and excludes patch validation. Current HARNESS_README/Starter and the pinned official SDK were re-read; hashes and claims are in OFFICIAL_BUDGET_EVIDENCE.json.

OFFICIAL_TASK_COUNT_UNKNOWN. The [organizer input description](https://www.kaggle.com/code/ryanholbrook/getting-started-gemma-4-developer-agent/input) says approximately 120 hidden tasks split evenly, not an exact count. Local 129 and SWE-bench 500 are not used as official N. All scales below are conditional stress tests. No private solutions/task rows were accessed.

## Verified and unknown boundaries

| Question | Evidence / conclusion |
|---|---|
| Exact global timer start/end | UNKNOWN; private controller source/timestamps are unavailable. The rule is known, exact implementation is not. |
| Sandbox preparation | Included globally; excluded from local Agent timer in SDK/README. |
| Model server startup | Whether it is inside the private charge boundary is UNKNOWN. Included conservatively in explicit startup allowances below. |
| Across tasks / Public and Private | Rule says all tasks; no evidence of separate 12-hour entitlements for each split. Actual task order/controller scheduling UNKNOWN. |
| Verification | Excluded from the stated generation budget. Local complete worker/Notebook wall time includes it, so must not replace generation cost. |
| Agent timeout | max_time_minutes is valid per-task Agent-loop wall time, not total task/global time. Commands also have a local remaining-time clamp. |
| eval_config | timeout_seconds, max_time_minutes, max_tool_calls and max_turns are supported inference fields. verification_timeout_seconds is local Phase 2; official table fixes scorer verification at 300s. |
| get_status | CPU/source-verified local session time/calls only; no official global remaining-time contract. |
| Global expiry and partial results | UNKNOWN; do not assume a completed prefix is guaranteed a partial score if the whole job exceeds runtime. |

The appropriate model is T_total=T_setup+T_model+sum(T_i), where T_i contains actual per-task setup and generation/patch collection, not Phase 2 validation. Actual private charged T_i remains UNKNOWN. The raw R12 generation proxy is used below as a sensitivity input, not relabeled official billing. Shared data/model hashing, imports and custom sandbox costs may differ from the scorer.

## Workload/time stress tests

Assumptions: shared startup/model allowance 1500s (kept from the prior conditional audit), reserves 0%, 5% and 10%. Reserve is one global allowance, not subtracted again per task. Safe average=(43200*(1-reserve)-1500)/N, including per-task setup. Full JSON contains 60 combinations of five N values, three reserves and four cost profiles.

| Assumed N | No reserve seconds/task | 5% reserve | 10% reserve | Capacity coverage at observed mean and 10% reserve |
|---:|---:|---:|---:|---:|
| 60 | 695.000 | 659.000 | 623.000 | 60/60 (100.0%) |
| 80 | 521.250 | 494.250 | 467.250 | 80/80 (100.0%) |
| 100 | 417.000 | 395.400 | 373.800 | 91/100 (91.0%) |
| 120 | 347.500 | 329.500 | 311.500 | 91/120 (75.8%) |
| 150 | 278.000 | 263.600 | 249.200 | 91/150 (60.7%) |

| Cost profile | Seconds/task | Capacity at 0% / 5% / 10% reserve, N=120 |
|---|---:|---|
| observed_R2_generation_mean | 406.924 | 102 / 97 / 91 |
| observed_R2_generation_median | 453.701 | 91 / 87 / 82 |
| observed_R2_generation_maximum | 468.921 | 88 / 84 / 79 |
| stress_480_agent_plus_60_task_setup | 540.000 | 77 / 73 / 69 |

At N=120 with 10% reserve, safe mean task cost is 311.5s. Compared with the 406.924s generation proxy this is a 23.45% reduction target. It is not a recommendation to silently cut max_time_minutes to that value: the cap is Agent-only and the success curve at shorter budgets is unknown. Median/max observed costs are based on only three selected development tasks, not tail quantiles. Stress 540s is 480s Agent plus an assumed 60s preparation, not a proven hard bound on a private task.

## Effective repairs rather than task coverage

Expected correct repairs is sum_i P(resolved_i | B_i, task_i, policy). N, the probabilities, how correctness changes with budget, runtime/success correlation, order and global-expiry effects are unknown. The JSON therefore keeps expected_resolved and probability curves null. It does not fit a success distribution from R2 development 3/3 and does not multiply that 3/3 by a capacity count.

Under a purely illustrative homogeneous fixed-cost assumption, increasing admitted coverage from 91 to 120 would require retaining more than 91/120 of the old per-task success probability to improve the expected repair count. In a continuous correct-repairs/time comparison the analogous cost ratio is 311.5/406.924≈0.7655. These are algebraic break-even conditions, not estimated probabilities, not permission to accept a correctness regression, and not an official score prediction. The requested experiment treats observed correctness loss as a non-advancement condition.

Observed R12 validated-repair/Agent or generation-proxy rates are descriptive only; official Native Resolved is null and no hidden-task generalization is inferred. The major risk is longer hidden tasks/preparation plus unknown global expiry behavior exhausting the full run before enough valid patches are delivered, potentially causing a whole-entry runtime error rather than a predictable lower coverage score.

## Practical conclusion

Keep the frozen eight-minute configuration unchanged in this audit. Test one policy that reduces low-value inference work while preserving focused target/control checks. Do not tune to prompt length, tool count, three easy tasks or a guessed exact N. Measure native validated yield and actual generation-scope costs on new independent tasks before revising a full-run budget.
