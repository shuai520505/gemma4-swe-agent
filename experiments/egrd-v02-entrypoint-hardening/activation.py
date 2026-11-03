"""Passive audit of actual ADK calls/responses; never parse prose as execution."""
import hashlib,json

def audit(events,available_tools,issue_sha256,state=None):
 calls=[];responses={}
 for event in sorted(events,key=lambda e:e['recorded_monotonic']):
  t=event['recorded_monotonic']
  for part in (event.get('event',{}).get('content') or {}).get('parts',[]):
   if 'function_call' in part:calls.append(dict(part['function_call'],time=t))
   if 'function_response' in part:
    r=part['function_response'];responses[r.get('id')]=dict(r,time=t)
 def success(r):return isinstance(r,dict) and not r.get('error') and r.get('status') not in ('error','warning')
 def summary(name):
  rows=[]
  for c in calls:
   if c['name']!=name:continue
   returned=responses.get(c.get('id'));body=returned.get('response',{}) if returned else None
   rows.append(dict(id=c.get('id'),called_monotonic=c['time'],args=c.get('args'),returned_monotonic=returned.get('time') if returned else None,response=body,status='TOOL_CALL_SUCCEEDED' if success(body) else 'TOOL_CALL_FAILED'))
  status='TOOL_NOT_AVAILABLE' if name not in available_tools else 'MODEL_DID_NOT_CALL' if not rows else 'TOOL_CALL_SUCCEEDED' if any(r['status']=='TOOL_CALL_SUCCEEDED' for r in rows) else 'TOOL_CALL_FAILED'
  return dict(status=status,calls=rows)
 load=summary('load_skill');script=summary('run_skill_script');inits=[];operations=[]
 for c in script['calls']:
  a=c.get('args') or {};payload=(a.get('args') or {}).get('request') if isinstance(a.get('args'),dict) else None
  try:req=json.loads(payload) if isinstance(payload,str) else {}
  except ValueError:req={}
  try:out=json.loads((c.get('response') or {}).get('stdout',''))
  except (ValueError,TypeError):out={}
  operation=dict(op=req.get('op'),time=c['called_monotonic'],request=req,response=out,status=c['status'])
  operations.append(operation)
  if req.get('op')=='init':
   exact=hashlib.sha256(str(req.get('original','')).encode()).hexdigest()==issue_sha256
   okay=c['status']=='TOOL_CALL_SUCCEEDED' and a.get('skill_name')=='egrd-repair' and a.get('file_path')=='scripts/egrd.py' and exact and out.get('schema')=='EGRD_V01' and out.get('phase')=='HYPOTHESIS' and out.get('result',{}).get('issue_sha256')==issue_sha256 and out.get('status') not in ['ADVISORY_CONTROL','UNKNOWN_OR_REFUSED']
   inits.append(dict(operation,success=okay))
 good_init=next((r for r in inits if r['success']),None)
 load_ok=next((r for r in load['calls'] if r['status']=='TOOL_CALL_SUCCEEDED' and (r['args'] or {}).get('skill_name')=='egrd-repair' and (r['response'] or {}).get('skill_name')=='egrd-repair'),None)
 order=bool(load_ok and good_init and len(calls)>=2 and calls[0]['name']=='load_skill' and calls[1]['name']=='run_skill_script' and good_init['time']>=load_ok['returned_monotonic'])
 excessive=len(load['calls'])>2 or len(inits)>2
 state_good=state is not None and state.get('contract',{}).get('original_sha256')==issue_sha256
 evidence=state.get('evidence',[]) if state_good else []
 edits=[dict(name=c['name'],time=c['time'],args=c.get('args'),response=responses.get(c.get('id'))) for c in calls if c['name'] in ['edit_file','write_file','run_command']]
 submits=summary('submit_patch')
 return dict(schema='EGRD_ACTIVATION_AUDIT_V2',execution_mode='PROMPT_ENFORCED_OPTIONAL_EXECUTION',load_skill=load,run_skill_script=script,submit_patch=submits,first_action_order_passed=order,bounded_attempts_passed=not excessive,contract_initialized=bool(good_init),activated=bool(order and not excessive and good_init),state_exported=state is not None,state_issue_hash_matches=state_good,evidence_records=len(evidence) if state_good else None,hypothesis_structure=bool(state_good and state.get('cause')),patch_intent=bool(state_good and state.get('patch_intent')),targeted_tests=[e for e in evidence if e.get('purpose')=='TARGET'],regression_tests=[e for e in evidence if e.get('purpose')=='REGRESSION'],diff_review=bool(state_good and state.get('diff_review_hash')==state.get('source_hash')),edit_and_command_calls=edits,operations=operations,semantic_issue_alignment='UNVERIFIED',native_resolved=None)
