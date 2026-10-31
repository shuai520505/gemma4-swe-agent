import json,zipfile,statistics,math,hashlib
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
z=zipfile.ZipFile(ROOT/'work/gemma-r12-01/gpu-run02-output/gemma-r12-authorized-gpu-02.zip')
co=[json.loads(l) for l in z.read('execution/events.jsonl').splitlines()]
stage={e['stage']:e['recorded_monotonic'] for e in co if e['kind']=='stage'}
observations=[]
for i,task in [(3,'django__django-11964'),(5,'pydata__xarray-6721'),(7,'pytest-dev__pytest-5631')]:
 p=f'execution/sessions/{i:02d}_R2_{task}/';row=json.loads(z.read(p+'SESSION_RESULT.json'))
 ev=[json.loads(l) for l in z.read(p+'events.jsonl').splitlines()];start=next(e['recorded_monotonic'] for e in ev if e.get('agent_started'))
 verify=next(e['recorded_monotonic'] for e in ev if e.get('stage')=='verification')
 persist=next(e['recorded_monotonic'] for e in ev if e.get('stage')=='persist')
 observations.append(dict(index=i,task=task,evidence='REAL_GPU_OBSERVATION',agent_seconds=row['agent_seconds'],
  worker_import_and_sandbox_setup_proxy_seconds=start-stage['session_'+str(i)],
  post_agent_save_proxy_seconds=verify-start-row['agent_seconds'],
  generation_scoped_task_cost_proxy_seconds=verify-stage['session_'+str(i)],
  excluded_independent_verification_seconds=persist-verify,
  command_time='Included in agent_seconds; not independently added',
  official_task_setup_seconds=None,official_measured_total_seconds=None))
agent=[r['agent_seconds'] for r in observations];cost=[r['generation_scoped_task_cost_proxy_seconds'] for r in observations]
scenarios=[]
profiles={'R2_mean_proxy':statistics.mean(cost),'R2_median_proxy':statistics.median(cost),'R2_slowest_observed_proxy':max(cost),'conservative_480_agent_plus_60_setup':540.0,'old_submission_60_minute_cap_plus_60_setup':3660.0}
for name,t in profiles.items():
 for reserve in [0,.1]:
  available=43200*(1-reserve)-900-600
  for n in [60,100,116,120,150,200]:
   cap=math.floor(available/t);safe=available/n
   scenarios.append(dict(profile=name,evidence='INFERENCE',assumed_tasks=n,task_count_is_official=False,setup_seconds_assumption=900,model_seconds_assumption=600,reserve_fraction=reserve,global_buffer_seconds=43200*reserve,task_cost_seconds=t,available_generation_seconds=available,average_per_task_budget_seconds=safe,capacity_tasks=cap,estimated_coverage_fraction=min(1,cap/n),mean_cost_reduction_fraction_required=max(0,1-safe/t),all_tasks_fit_under_assumptions=n*t<=available))
doc=dict(status='OFFICIAL_TASK_COUNT_UNKNOWN',sample_size=3,official_exact_task_count=None,official_approximate_task_count=120,
 approximate_count_source='Organizer Getting Started input/data description says about 120, evenly split. Exact count is not disclosed/verified; public leaderboard says approximately half.',
 public_private_budget='Official all-tasks 12-hour wording is the planning scope; no separate 12-hour entitlement for each split has been verified.',
 official_order=None,global_timer_implementation=None,global_get_status_supported=False,official_server_start_charge_boundary=None,
 official_rules=dict(total_patch_generation_seconds=43200,sandbox_setup_included=True,patch_validation_excluded=True,per_task_limits_optional=True),
 observations=observations,observed_shared_prepare_seconds=stage['load_model']-stage['prepare_agent'],observed_model_load_seconds=json.loads(z.read('execution/MODEL_LOAD_COMPLETED.json'))['seconds'],
 observed_model_stage_seconds=stage['session_1']-stage['load_model'],
 agent_summary=dict(mean=statistics.mean(agent),median=statistics.median(agent),maximum=max(agent)),task_cost_proxy_summary=dict(mean=statistics.mean(cost),median=statistics.median(cost),maximum=max(cost)),
 formula='T_total = T_setup + T_model + sum(T_i). T_i includes per-task setup, agent/model/tool time and patch extraction; excludes separate patch verification. No double counting tool time.',
 caveat='R12 uses a custom non-root research sandbox and dedicated evaluator, not the private scorer. Three chosen development tasks do not estimate the hidden cost distribution reliably. Profile capacities are arithmetic conditional scenarios, not predictions or guaranteed completions. Setup/model assumptions are explicit stress allowances, not official measurements.',
 scenarios=scenarios,decision='R2_BLOCKED_BY_BUDGET',reason='No demonstrated safe coverage of the approximate full hidden workload at unchanged 8-minute cap. Exact count, private scorer overhead and global admission logic remain unknown. Do not silently change frozen eval_config.')
(OUT/'R2_BUDGET_ANALYSIS.json').write_text(json.dumps(doc,indent=2)+'\n',encoding='utf8')
lines=['# R2 global 12-hour budget audit','','OFFICIAL_RULE: all-task patch generation is limited to 43200 seconds, including sandbox setup and excluding patch validation. Per-task operational limits are optional. [Official overview](https://www.kaggle.com/competitions/gemma-4-developer-agent/overview).','',
 'OFFICIAL_TASK_COUNT_UNKNOWN: the [organizer Starter input/data description](https://www.kaggle.com/code/ryanholbrook/getting-started-gemma-4-developer-agent/input) describes about 120 hidden tasks split evenly; the [official leaderboard](https://www.kaggle.com/competitions/gemma-4-developer-agent/leaderboard) says roughly half is public. Neither is an exact task count. No hidden task rows or solutions were accessed. Do not use local 129 or SWE-bench 500 as official N, or assume only the public half consumes the budget. A separately allocated 12 hours per split is not established.','',
 'STATIC_ANALYSIS: the freshly downloaded official Starter reads eval_config fields, loops over a local sample tasks[:2], and evaluates both phases. That sample loop is not the private scoring controller. Frozen SDK sources enforce per-session budgets. The actual private all-task timer, task ordering, partial-output timeout policy and its model-start boundary are UNKNOWN.','',
 '## What R12 actually measures','', '| Task | Agent seconds | Import/setup proxy | Save proxy | Counted task proxy | Excluded verifier |','|---|---:|---:|---:|---:|---:|']
for r in observations:lines.append('| '+r['task']+' | '+' | '.join(f"{r[k]:.3f}" for k in ['agent_seconds','worker_import_and_sandbox_setup_proxy_seconds','post_agent_save_proxy_seconds','generation_scoped_task_cost_proxy_seconds','excluded_independent_verification_seconds'])+' |')
lines+=['',f"REAL_GPU_OBSERVATION (n=3): Agent mean {statistics.mean(agent):.3f}s, median {statistics.median(agent):.3f}s, slowest {max(agent):.3f}s. Generation-scoped task proxy mean {statistics.mean(cost):.3f}s, median {statistics.median(cost):.3f}s, slowest {max(cost):.3f}s.",
 f"Observed coordinator prepare {doc['observed_shared_prepare_seconds']:.3f}s; model-load receipt {doc['observed_model_load_seconds']:.3f}s, model stage {doc['observed_model_stage_seconds']:.3f}s. Earlier Notebook installation/bootstrap and official setup transfer costs are not isolated to an official chargeable timer. They are UNKNOWN, not zero.",
 'Agent wall time already includes inference waits and tool execution; summing these again would double count. submit_patch call/response time lies inside the Agent interval; native patch collection before verifier is included in the save proxy. Independent Phase 2 verifier time is shown but excluded from the budget model. Worker persistence, observer overhead, server cleanup and evidence archive time are not automatically official chargeable costs. Notebook total wall-clock is not used as sum(T_i).',
 '', '## Conditional capacity, not a forecast','',
 'INFERENCE assumptions for the table: T_setup=900s, T_model=600s. These are explicit conservative allowances, not measured scorer facts. Reserve 4320s (10%) for setup variance, final output/persistence and shutdown. Never consume that same buffer twice. A 480s Agent cap plus assumed 60s per-task setup gives a 540s planning cost, not a proven strict upper bound.',
 '', '| Profile | Cost/task | Capacity, no reserve | Capacity, 10% reserve | Coverage at assumed N=120 with reserve |','|---|---:|---:|---:|---:|']
for name,t in profiles.items():
 no=next(r for r in scenarios if r['profile']==name and r['reserve_fraction']==0 and r['assumed_tasks']==120)
 safe=next(r for r in scenarios if r['profile']==name and r['reserve_fraction']==.1 and r['assumed_tasks']==120)
 lines.append(f"| {name} | {t:.2f}s | {no['capacity_tasks']} | {safe['capacity_tasks']} | {safe['estimated_coverage_fraction']:.1%} |")
lines+=['','For general N: B_avg=(43200-T_setup-T_model)/N; B_safe=(38880-T_setup-T_model)/N. If setup/model start is outside the official charge boundary, capacity is higher; this has not been verified, so it is a sensitivity, not a reason to omit startup.','', '| Assumed N | B_avg | B_safe | Mean proxy reduction needed |','|---:|---:|---:|---:|']
for n in [60,100,116,120,150,200]:
 s=next(r for r in scenarios if r['profile']=='R2_mean_proxy' and r['reserve_fraction']==.1 and r['assumed_tasks']==n)
 lines.append(f"| {n} | {(43200-1500)/n:.2f}s | {s['average_per_task_budget_seconds']:.2f}s | {s['mean_cost_reduction_fraction_required']:.1%} |")
lines+=['', 'At assumed N=120 the safe total task budget is 311.5s, including per-task preparation, rather than 480s of Agent work alone. The current frozen eight-minute cap is not a global coverage guarantee. Completion rate also is not repair rate: processing every task does not imply passing every hidden check.',
 'UNKNOWN: task cost distribution, exact N, official setup latency, scorer timeout failure/partial-score behavior and task ordering. Missing patches have no successful repair evidence; the docs describe empty-patch handling, but an all-notebook runtime failure must not be treated as a guaranteed score for the completed prefix.',
 '', '## Decision','', 'R2_BLOCKED_BY_BUDGET for immediate unchanged full-workload dispatch. R2 is a promising reviewable candidate, but safe hidden coverage is not demonstrated. Preserve the exact package and require a separately authorized budget experiment/protocol before changing its cap. This audit changes no Agent configuration.']
(OUT/'R2_BUDGET_ANALYSIS.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
print(json.dumps(doc['task_cost_proxy_summary']))
