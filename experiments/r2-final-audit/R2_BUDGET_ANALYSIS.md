# R2 global 12-hour budget audit

OFFICIAL_RULE: all-task patch generation is limited to 43200 seconds, including sandbox setup and excluding patch validation. Per-task operational limits are optional. [Official overview](https://www.kaggle.com/competitions/gemma-4-developer-agent/overview).

OFFICIAL_TASK_COUNT_UNKNOWN: the [organizer Starter input/data description](https://www.kaggle.com/code/ryanholbrook/getting-started-gemma-4-developer-agent/input) describes about 120 hidden tasks split evenly; the [official leaderboard](https://www.kaggle.com/competitions/gemma-4-developer-agent/leaderboard) says roughly half is public. Neither is an exact task count. No hidden task rows or solutions were accessed. Do not use local 129 or SWE-bench 500 as official N, or assume only the public half consumes the budget. A separately allocated 12 hours per split is not established.

STATIC_ANALYSIS: the freshly downloaded official Starter reads eval_config fields, loops over a local sample tasks[:2], and evaluates both phases. That sample loop is not the private scoring controller. Frozen SDK sources enforce per-session budgets. The actual private all-task timer, task ordering, partial-output timeout policy and its model-start boundary are UNKNOWN.

## What R12 actually measures

| Task | Agent seconds | Import/setup proxy | Save proxy | Counted task proxy | Excluded verifier |
|---|---:|---:|---:|---:|---:|
| django__django-11964 | 435.903 | 17.366 | 0.432 | 453.701 | 10.969 |
| pydata__xarray-6721 | 448.042 | 20.696 | 0.183 | 468.921 | 10.136 |
| pytest-dev__pytest-5631 | 277.930 | 20.040 | 0.181 | 298.151 | 8.751 |

REAL_GPU_OBSERVATION (n=3): Agent mean 387.292s, median 435.903s, slowest 448.042s. Generation-scoped task proxy mean 406.924s, median 453.701s, slowest 468.921s.
Observed coordinator prepare 236.483s; model-load receipt 304.382s, model stage 306.596s. Earlier Notebook installation/bootstrap and official setup transfer costs are not isolated to an official chargeable timer. They are UNKNOWN, not zero.
Agent wall time already includes inference waits and tool execution; summing these again would double count. submit_patch call/response time lies inside the Agent interval; native patch collection before verifier is included in the save proxy. Independent Phase 2 verifier time is shown but excluded from the budget model. Worker persistence, observer overhead, server cleanup and evidence archive time are not automatically official chargeable costs. Notebook total wall-clock is not used as sum(T_i).

## Conditional capacity, not a forecast

INFERENCE assumptions for the table: T_setup=900s, T_model=600s. These are explicit conservative allowances, not measured scorer facts. Reserve 4320s (10%) for setup variance, final output/persistence and shutdown. Never consume that same buffer twice. A 480s Agent cap plus assumed 60s per-task setup gives a 540s planning cost, not a proven strict upper bound.

| Profile | Cost/task | Capacity, no reserve | Capacity, 10% reserve | Coverage at assumed N=120 with reserve |
|---|---:|---:|---:|---:|
| R2_mean_proxy | 406.92s | 102 | 91 | 75.8% |
| R2_median_proxy | 453.70s | 91 | 82 | 68.3% |
| R2_slowest_observed_proxy | 468.92s | 88 | 79 | 65.8% |
| conservative_480_agent_plus_60_setup | 540.00s | 77 | 69 | 57.5% |
| old_submission_60_minute_cap_plus_60_setup | 3660.00s | 11 | 10 | 8.3% |

For general N: B_avg=(43200-T_setup-T_model)/N; B_safe=(38880-T_setup-T_model)/N. If setup/model start is outside the official charge boundary, capacity is higher; this has not been verified, so it is a sensitivity, not a reason to omit startup.

| Assumed N | B_avg | B_safe | Mean proxy reduction needed |
|---:|---:|---:|---:|
| 60 | 695.00s | 623.00s | 0.0% |
| 100 | 417.00s | 373.80s | 8.1% |
| 116 | 359.48s | 322.24s | 20.8% |
| 120 | 347.50s | 311.50s | 23.5% |
| 150 | 278.00s | 249.20s | 38.8% |
| 200 | 208.50s | 186.90s | 54.1% |

At assumed N=120 the safe total task budget is 311.5s, including per-task preparation, rather than 480s of Agent work alone. The current frozen eight-minute cap is not a global coverage guarantee. Completion rate also is not repair rate: processing every task does not imply passing every hidden check.
UNKNOWN: task cost distribution, exact N, official setup latency, scorer timeout failure/partial-score behavior and task ordering. Missing patches have no successful repair evidence; the docs describe empty-patch handling, but an all-notebook runtime failure must not be treated as a guaranteed score for the completed prefix.

## Decision

R2_BLOCKED_BY_BUDGET for immediate unchanged full-workload dispatch. R2 is a promising reviewable candidate, but safe hidden coverage is not demonstrated. Preserve the exact package and require a separately authorized budget experiment/protocol before changing its cap. This audit changes no Agent configuration.
