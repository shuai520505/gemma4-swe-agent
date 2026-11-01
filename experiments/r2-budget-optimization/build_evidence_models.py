import json,hashlib,zipfile,statistics,math,collections
from pathlib import Path
from datetime import datetime,timezone
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
sha=lambda b:hashlib.sha256(b).hexdigest()
def save(name,d):(OUT/name).write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
T=json.loads((OUT/'R2_TIME_DECOMPOSITION.json').read_bytes());A=json.loads((OUT/'R2_TOOL_ACTION_AUDIT.json').read_bytes())

# Only the old model's tool trajectories and native result summaries are read.
# No reference solution or evaluator test overlay is accessed.
history_root=Path('D:/kaggle/Gemma 4 Developer Agent Competition/gemma4-egrd-v01/u_re/v01/experiments/action_priority_01/real_gemma_abba03')
hreg=json.loads((history_root/'RAW_ARCHIVES.json').read_bytes());hzpath=Path(hreg['GPU03']['private_path']);assert sha(hzpath.read_bytes())==hreg['GPU03']['sha256']
history=[]
with zipfile.ZipFile(hzpath) as hz:
 assert hz.testzip() is None
 native=json.loads(hz.read('results/ABBA_RESULTS.json'))
 for n in sorted(n for n in hz.namelist() if n.startswith('results/runs/') and n.endswith('/agent/adk_events.jsonl')):
  calls=[];byid={};responses={}
  for ln,l in enumerate(hz.read(n).splitlines(),1):
   e=json.loads(l)
   for part in (e.get('event',e).get('content') or {}).get('parts',[]):
    f=part.get('function_call');r=part.get('function_response')
    if f and f['id'] not in byid:
     v=dict(call_id=f['id'],tool=f['name'],args=f.get('args',{}),line=ln,monotonic=e.get('recorded_monotonic'));calls.append(v);byid[f['id']]=v
    if r:responses[r['id']]=r.get('response')
  idx=next((i for i,c in enumerate(calls) if c['tool']=='submit_patch'),None)
  submits=[dict(call=c,response=responses.get(c['call_id'])) for c in calls if c['tool']=='submit_patch']
  after=[] if idx is None else calls[idx+1:]
  errors=[dict(call_id=c['call_id'],tool=c['tool'],response=responses[c['call_id']]) for c in calls if isinstance(responses.get(c['call_id']),dict) and (responses[c['call_id']].get('status')=='error' or responses[c['call_id']].get('error'))]
  dup=[];seen={}
  for c in calls:
   body=responses.get(c['call_id']) or {};body={k:v for k,v in body.items() if k!='budget_warning'} if isinstance(body,dict) else body
   key=(c['tool'],json.dumps(c['args'],sort_keys=True),json.dumps(body,sort_keys=True))
   if key in seen:dup.append(dict(prior_call=seen[key],call_id=c['call_id'],args=c['args'],tool=c['tool'],interpretation='Identical tool arguments and result. Environmental/semantic necessity still requires review.'))
   seen[key]=c['call_id']
  history.append(dict(member=n,sha256=sha(hz.read(n)),tool_count=len(calls),submit_count=len(submits),submits=submits,post_first_submit_calls=after,identical_argument_and_response_repeats=dup,errors=errors))
save('ACTION_FIRST_CORROBORATION.json',dict(archive_sha256=sha(hzpath.read_bytes()),archive_path=str(hzpath),CRC_pass=True,native_summaries=[dict(run=r['run'],instance_id=r['instance_id'],arm=r['arm'],native_resolved=r['native']['resolved'],agent_error=r['native'].get('agent_error')) for r in native['records']],sessions=history,
 conclusions=['fastapi_9425-A had only diagnostic changes and a context reservation rejection; fastapi_14786-A also had a context rejection but a retained valid patch. Do not attribute both solely to lack of early action.',
 'fastapi_14786-A repeats two git diff calls and another submit after an initial successful 404-byte one-file submission, then checks git status; same-result repeats are observed. This is corroborating finalization-cost evidence, not proof that all post-submit actions are useless.',
 'Wider pytest collection encountered missing python-multipart. Focused follow-up tests add real information; do not delete them just because they follow a failed command.',
 'This older study used different prompts, budgets, tools/output limits and a context guard. Do not pool its effects with R12 or claim the two FastAPI tasks are new holdouts.']))

sourcefiles={}
for p in [OUT/'official-source/HARNESS_README.md',*list((OUT/'official-source/starter').glob('*.ipynb'))]:
 assert p.is_file();sourcefiles[str(p.relative_to(OUT))]=sha(p.read_bytes())
sdkroot=ROOT/'work/r2-audit/official-sources'
for rel in ['swegemma/config.py','swegemma/context.py','swegemma/tools/base.py','swegemma/tools/execution.py','swegemma/harness/agent_runner.py']:
 p=sdkroot/rel;sourcefiles['pinned_sdk/'+rel]=sha(p.read_bytes())
save('OFFICIAL_BUDGET_EVIDENCE.json',dict(read_at_utc=datetime.now(timezone.utc).isoformat(),sources=[
 dict(url='https://www.kaggle.com/competitions/gemma-4-developer-agent/overview',claim='All tasks share 12h to submit patches, inclusive of sandbox setup and exclusive of patch validation. Exact private implementation boundaries are not disclosed by this wording.'),
 dict(url='https://www.kaggle.com/code/ryanholbrook/getting-started-gemma-4-developer-agent',claim='Fresh CLI source downloaded read-only; explicitly parses per-task eval settings then runs two published examples. That sample loop is not the hidden scoring controller.'),
 dict(url='https://www.kaggle.com/code/ryanholbrook/getting-started-gemma-4-developer-agent/input',claim='Organizer description says about 120 hidden tasks split evenly. Exact N remains unknown; local 129 is development data.'),
 dict(url='https://www.kaggle.com/competitions/gemma-4-developer-agent/data',claim='Fresh HARNESS_README read via authenticated CLI, not hidden task contents. Section 7.1 documents inference keys, session timing and fixed scorer verification timeout.')],
 source_sha256=sourcefiles,official_exact_tasks=None,task_count_status='OFFICIAL_TASK_COUNT_UNKNOWN',
 fields=dict(timeout_seconds='Supported per-command ceiling; actual execution clamps to current session remaining time with the documented minimum-floor behavior.',max_time_minutes='Supported per-task Agent loop minutes; starts after sandbox preparation.',max_tool_calls='Supported charged-tool count; excludes get_status and submit_patch.',max_turns='Supported per-task model-turn cap; not a global clock.',verification_timeout_seconds='Local EvalConfig/Starter Phase 2 setting; fixed 300 seconds on scorer, not a submission-controlled Stage 1 field.'),
 global_clock=dict(total_seconds=43200,sandbox_preparation_included=True,verification_excluded=True,all_tasks_scope=True,model_server_start_charge_boundary=None,precise_start_event=None,precise_end_event=None,private_timer_source=None,task_order=None,global_budget_in_get_status=False),
 source_caveat='Web search excerpts have their reported crawl age; fresh CLI sources and pinned official SDK are separately hashed. No third-party estimates, leaderboard reverse-engineering or hidden solution data are used.'))

profiles={}
r2=[s for s in T['sessions'] if s['candidate']=='R2'];cost=[s['phase1_generation_cost_proxy_seconds'] for s in r2]
profiles['observed_R2_generation_mean']=statistics.mean(cost);profiles['observed_R2_generation_median']=statistics.median(cost);profiles['observed_R2_generation_maximum']=max(cost);profiles['stress_480_agent_plus_60_task_setup']=540.0
scenarios=[]
for n in [60,80,100,120,150]:
 for reserve in [0,.05,.10]:
  available=43200*(1-reserve)-1500;per=available/n
  for profile,c in profiles.items():
   m=min(n,math.floor(available/c))
   scenarios.append(dict(assumed_N=n,task_count_is_official=False,reserve_fraction=reserve,global_safety_seconds=43200*reserve,setup_model_assumption_seconds=1500,available_generation_seconds=available,safe_mean_total_task_seconds=per,profile=profile,assumed_cost_seconds=c,conditional_capacity_tasks=m,conditional_coverage_fraction=m/n,required_cost_reduction_fraction=max(0,1-per/c),expected_resolved=None,success_probability_curve=None,conditional_expected_resolved_bounds=[0,m],
    completion_caveat='This constant-cost admission scenario presumes the completed prefix is retained. Actual private total-timeout/partial-output handling and workload ordering are UNKNOWN; no official score is promised.'))
save('R2_BUDGET_MODEL.json',dict(evidence_classes=['REAL_GPU_OBSERVATION','OFFICIAL_RULE','STATIC_ANALYSIS','INFERENCE','UNKNOWN'],task_count_status='OFFICIAL_TASK_COUNT_UNKNOWN',official_exact_N=None,total_seconds=43200,
 real_official_R2_charged_seconds=None,raw_reconciliation=T['reconciliation'],sample_size=3,
 formula='T_total = T_setup + T_model + sum(T_i); T_i includes task setup, Agent/tool/model waits and patch collection within the official generation scope. Independent verification is excluded.',
 objective='Maximize sum_i P(resolved_i | B_i, task_i, policy) subject to the official total generation-time budget and correctness guardrails.',
 unknown_parameters=['N','Private charge start/end and model-start boundary','Per-task official setup costs','Success probability as a function of budget/task','Cost tail and correlation of difficulty, runtime and success','Order and censoring from global expiry','Full-job timeout and partial-output scoring semantics'],
 estimated_hidden_success_probabilities=None,expected_hidden_resolved_count=None,
 proxy_profiles=profiles,scenarios=scenarios,
 illustrative_break_even=dict(meaning='Algebra only under homogeneous success and fixed mean cost assumptions, not fitted probabilities or an acceptance rule permitting correctness loss.',at_N120_reserve10_original_capacity=91,new_hypothetical_full_coverage=120,coverage_only_success_retention_threshold=91/120,continuous_rate_success_retention_threshold=311.5/statistics.mean(cost)),
 no_fabricated_probability_distribution=True,no_budget_change_implemented=True))

def group_cost(session,ordinals):
 s=next(s for s in A['sessions'] if s['index']==session);actions=[a for a in s['actions'] if a['ordinal'] in ordinals];assert len(actions)==len(ordinals)
 return dict(session=session,ordinals=ordinals,observed_tool_envelope_seconds=sum(a['observed_tool_envelope_seconds'] or 0 for a in actions),associated_HTTP_roundtrip_seconds=sum(a['http_roundtrip_seconds'] for a in actions),call_ids=[a['id'] for a in actions],
  savings_if_removed_seconds=None,caveat='Measured exposure, not counterfactual savings. Additional inference/tests would replace some work; these sets can overlap phase windows and must not be summed as total removable time.')
bench=[]
for r in r2:
 event=r['events'];bench.append(dict(session=r['index'],first_edit_interval=event['T3_first_production_edit_interval'],observed_hypothesis_proxy=event['T2_observable_hypothesis_proxy'],gap_to_first_edit=r['hypothesis_to_first_edit_interval_seconds']))
invalid=[group_cost(s['index'],[a['ordinal'] for a in s['actions'] if a['category']=='无效测试']) for s in A['sessions'] if s['candidate']=='R2']
badparams=[group_cost(s['index'],[a['ordinal'] for a in s['actions'] if a['category']=='参数错误编辑']) for s in A['sessions'] if s['schema_errors']]
save('BOTTLENECK_EVIDENCE.json',dict(rankings=[
 dict(rank=1,name='Source-backed hypotheses are followed by long additional inference/read/simulation chains before production edits',raw_evidence=bench,R2_sessions_affected=3,causality='Outcome association only. R1 xarray never edits; BASELINE Django/xarray fail to repair. Earlier internal readiness is not known.',potential_intervention='Candidate A evidence-gated minimal edit decision; never a mandatory blind edit.',guaranteed_savings_seconds=None,risk='Premature edit with wrong mechanism or untested assumptions; loss of repair correctness.'),
 dict(rank=2,name='Malformed or misbound verification and repeated diagnostic construction consume inference rounds without a passing target check',raw_evidence=invalid,R2_failed_test_operations=sum(len(x['ordinals']) for x in invalid),additional_misbound_operations=[group_cost(7,[3,10])],potential_intervention='Ground the smallest discriminating probe in the actual production path and preserve required controls; fixture and target failures must be distinct.',guaranteed_savings_seconds=None,risk='Deleting a failing command that actually reproduces the bug, or suppressing legitimate environment/compatibility evidence.'),
 dict(rank=3,name='Recovery and finalization rework: malformed edits, production reversals and premature mixed-scope/empty submissions',R2_counterfactual_edit_cycle=group_cost(3,[17,18,19,20]),R2_optional_control_and_cycle_window=group_cost(3,[15,16,17,18,19,20]),BASELINE_schema_failures=badparams,R1_scope_correction=group_cost(2,[24,25,26,27,28]),potential_intervention='Candidate B version-bound verification and scope-aware one-time finalization, after necessary checks; retain a corrective submit when the patch truly changes.',guaranteed_savings_seconds=None,risk='Skipping necessary revalidation after a real source/test-input change or failing to remove diagnostic files.')],
 R2_agent_HTTP_fraction=sum(r['http_request_roundtrip_union_inside_agent_seconds'] for r in r2)/sum(r['agent_execution_seconds'] for r in r2),R2_agent_tool_envelope_fraction=sum(r['tool_call_envelope_union_inside_agent_seconds'] for r in r2)/sum(r['agent_execution_seconds'] for r in r2),
 note='This ordering is a research priority, not a statistically estimated causal ranking. SDK compaction overhead is measured but remains a frozen infrastructure setting, not a third proposed candidate.'))

protected=json.loads((OUT/'FROZEN_INPUT_IDENTITIES.json').read_bytes())
protected[str(hzpath)]=sha(hzpath.read_bytes());protected[str(history_root/'RAW_ARCHIVES.json')]=sha((history_root/'RAW_ARCHIVES.json').read_bytes())
save('HISTORY_ADDITIONAL_IDENTITIES.json',{p:h for p,h in protected.items() if p not in json.loads((OUT/'FROZEN_INPUT_IDENTITIES.json').read_bytes())})
print(json.dumps(dict(profiles=profiles,R2_HTTP_fraction=sum(r['http_request_roundtrip_union_inside_agent_seconds'] for r in r2)/sum(r['agent_execution_seconds'] for r in r2),scenarios=len(scenarios),invalid_probe_groups=invalid,malformed_edit_groups=badparams),indent=2))
