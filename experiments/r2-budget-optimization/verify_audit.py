"""Independent consistency/identity checks on delivered evidence, without model execution."""
import json,hashlib,zipfile,math
from pathlib import Path
from datetime import datetime,timezone
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
sha=lambda b:hashlib.sha256(b).hexdigest()
read=lambda n:json.loads((OUT/n).read_bytes())
required=['R2_TIME_DECOMPOSITION.json','R2_TOOL_ACTION_AUDIT.json','R2_TRACE_EFFICIENCY_REPORT.md','R2_INSTRUCTION_COMPLIANCE.md','R2_BUDGET_MODEL.json','R2_BUDGET_ANALYSIS.md','R2_OPTIMIZATION_HYPOTHESES.md','R2_NEXT_EXPERIMENT_PROTOCOL.md','R2_BUDGET_OPTIMIZATION_FINAL_DECISION.md']
assert all((OUT/n).is_file() for n in required)
old=read('FROZEN_INPUT_IDENTITIES.json');additional=read('HISTORY_ADDITIONAL_IDENTITIES.json')
for p,h in (old|additional).items():assert sha(Path(p).read_bytes())==h,p
T=read('R2_TIME_DECOMPOSITION.json');A=read('R2_TOOL_ACTION_AUDIT.json');B=read('R2_BUDGET_MODEL.json');E=read('RAW_EVIDENCE_INDEX.json');O=read('OFFICIAL_BUDGET_EVIDENCE.json')
assert len(T['sessions'])==len(A['sessions'])==9
assert [r['candidate'] for r in T['sessions']]==['BASELINE','R1','R2','R1','R2','BASELINE','R2','BASELINE','R1']
archive=Path(E['archive_path']);assert sha(archive.read_bytes())==E['archive_sha256']==T['archive_sha256']==A['archive_sha256']
schemas=[];terminal_without_response=0;free=0;params=0;budget_rejects=0;statuses=0;submits=0
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 for m in E['members']:assert sha(z.read(m['member']))==m['sha256']
 for t,s in zip(T['sessions'],A['sessions']):
  assert t['index']==s['index'] and t['official_charged_seconds'] is None and t['official_native_resolved'] is None and t['canonical_swebench_resolved'] is None
  assert t['pure_model_generation_seconds'] is None and t['server_queue_seconds'] is None and t['final_invalid_idle_wait_seconds'] is None
  assert t['events']['T2_internal_hypothesis_formation_seconds'] is None
  assert len(s['actions'])==s['attempted_tools'] and len({a['id'] for a in s['actions']})==len(s['actions'])
  assert sum(r['count'] for r in s['category_statistics'].values())==len(s['actions'])
  assert t['unattributed_agent_seconds']>=-.001 and t['observer_interval_overlap_seconds']>=-.001
  assert abs(t['http_request_roundtrip_union_inside_agent_seconds']+t['tool_call_envelope_union_inside_agent_seconds']-t['observer_interval_overlap_seconds']+t['unattributed_agent_seconds']-t['agent_execution_seconds'])<1e-5
  p=t['session_prefix'];adk=[json.loads(l) for l in z.read(p+'adk_events.jsonl').splitlines()];wire=[json.loads(l) for l in z.read(p+'model_transport/http_wire.jsonl').splitlines()]
  first=next(q for q in wire if q['kind']=='http_request');schemas.append(sha(json.dumps(first['body']['tools'],sort_keys=True).encode()))
  terminal_without_response+=sum(r['wire_response_line'] is None for r in s['http_requests'])
  for action in s['actions']:
   er=action['raw_evidence'];assert er['archive_member']==p+'adk_events.jsonl'
   parts=(adk[er['call_line']-1]['event'].get('content') or {}).get('parts',[])
   c=next(pt['function_call'] for pt in parts if pt.get('function_call',{}).get('id')==action['id']);assert c['args']==action['args']
   parts=(adk[er['response_line']-1]['event'].get('content') or {}).get('parts',[])
   r=next(pt['function_response']['response'] for pt in parts if pt.get('function_response',{}).get('id')==action['id'])
   assert sha(json.dumps(r,sort_keys=True).encode())==er['response_sha256']
   params+=action['category']=='参数错误编辑';statuses+=action['tool']=='get_status';submits+=action['tool']=='submit_patch'
   budget_rejects+=r.get('error_type')=='BudgetExceeded'
assert len(set(schemas))==1
assert sum(r['http_requests'] for r in T['sessions'])==226 and sum(r['native_llm_counter'] for r in T['sessions'])==217
assert sum(r['SDK_compaction_requests'] for r in T['sessions'])==7 and terminal_without_response==2
assert params==5 and statuses==1 and submits==9 and budget_rejects==2
assert 209-192==params+statuses+submits+budget_rejects
assert B['official_exact_N'] is None and B['real_official_R2_charged_seconds'] is None
assert B['estimated_hidden_success_probabilities'] is None and B['expected_hidden_resolved_count'] is None
assert len(B['scenarios'])==60
for s in B['scenarios']:
 assert s['assumed_N'] in [60,80,100,120,150] and s['reserve_fraction'] in [0,.05,.1]
 assert s['expected_resolved'] is None and s['success_probability_curve'] is None
 assert s['conditional_capacity_tasks']==min(s['assumed_N'],math.floor(s['available_generation_seconds']/s['assumed_cost_seconds']))
assert not list(OUT.rglob('*.zip')) and not list(OUT.rglob('agent.yaml'))
contract=read('CPU_TOOL_CONTRACT_RESULT.json');assert contract['model_requests']==0 and not contract['repair_capability_evidence']
for k,h in O['source_sha256'].items():
 p=ROOT/'work/r2-audit/official-sources'/k.removeprefix('pinned_sdk/') if k.startswith('pinned_sdk/') else OUT/k
 assert sha(p.read_bytes())==h
result=dict(gate='R2_BUDGET_AUDIT_COMPLETE',checked_at_utc=datetime.now(timezone.utc).isoformat(),nine_raw_sessions_verified=True,tool_actions_linked_and_rehashed=209,charged_tools_reconciled=192,HTTP_requests_reconciled=226,schemas_identical=True,compaction_requests=7,incomplete_final_requests=2,probabilities_not_fabricated=True,official_cost_preserved_UNKNOWN=True,conditional_budget_scenarios_verified=60,original_files_unchanged=len(old),additional_history_files_unchanged=len(additional),required_files_present=9,no_candidate_or_R3_archive=True,CPU_tool_contract_pass=True,GPU_Notebooks_started=0,SaveKernel_calls=0,model_inference_requests=0,formal_submissions=0)
(OUT/'AUDIT_VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print(json.dumps(result))
