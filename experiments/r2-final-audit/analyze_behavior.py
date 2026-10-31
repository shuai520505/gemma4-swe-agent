import collections,hashlib,json,re
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
Z=ROOT/'work/gemma-r12-01/gpu-run02-output/gemma-r12-authorized-gpu-02.zip'
old=json.loads((ROOT/'outputs/r12_gpu_run02/R12_GPU_RESULTS.json').read_bytes())
result=[]
with zipfile.ZipFile(Z) as z:
 for row in old['sessions']:
  i=row['index'];p=f"execution/sessions/{i:02d}_{row['candidate']}_{row['instance_id']}/"
  es=[json.loads(l) for l in z.read(p+'events.jsonl').splitlines()]
  start=next(x['recorded_monotonic'] for x in es if x.get('agent_started'))
  calls={};responses={};ordered=[]
  for l in z.read(p+'adk_events.jsonl').splitlines():
   event=json.loads(l);sec=event['recorded_monotonic']-start
   for part in (event.get('event',{}).get('content') or {}).get('parts',[]):
    f=part.get('function_call');r=part.get('function_response')
    if f and f['id'] not in calls:
     item=dict(id=f['id'],tool=f['name'],args=f.get('args',{}),call_observed_seconds=sec)
     calls[f['id']]=item;ordered.append(item)
    if r:responses[r['id']]=dict(response_observed_seconds=sec,response=r.get('response'))
  for c in ordered:c.update(responses.get(c['id'],dict(response=None,response_observed_seconds=None)))
  production=set(row['evaluation'].get('changed_files',[]))
  edits=[c for c in ordered if c['tool'] in ('edit_file','write_file') and c['args'].get('filepath') in production and (c.get('response') or {}).get('status')=='ok']
  statuses=[c for c in ordered if c['tool']=='get_status'];submit=[c for c in ordered if c['tool']=='submit_patch']
  commands=[c for c in ordered if c['tool']=='run_command'];errors=[c for c in ordered if (c.get('response') or {}).get('status')=='error' or (c.get('response') or {}).get('error')]
  repeats=[];seen={}
  for c in commands:
   key=c['args'].get('command','');prior=seen.get(key)
   if prior is not None:repeats.append(dict(prior_call=prior,repeat_call=c['id'],command=key,unnecessary='UNKNOWN; repeated verification can be justified after a source change'))
   seen[key]=c['id']
  last=submit[-1] if submit else None
  local=next((c for c in ordered if c['tool']=='read_file' and any(s in c['args'].get('filepath','') for s in ('models/enums.py','core/common.py','_pytest/compat.py'))),None)
  result.append(dict(index=i,candidate=row['candidate'],task=row['instance_id'],evidence='REAL_GPU_OBSERVATION',
   first_localization_exact_seconds=None,first_relevant_source_read_proxy_seconds=local['response_observed_seconds'] if local else None,
   localization_caveat='First relevant file read is observable; internal model localization/understanding has no exact timestamp.',
   get_status_calls=len(statuses),get_status_responses=statuses,first_production_edit=row['metrics']['first_production_edit'],
   last_observed_successful_production_edit_call=edits[-1] if edits else None,last_edit_exact_seconds=None,
   last_edit_caveat='Successful edit response bounds the tool operation; passive observer only recorded first change. No fabricated exact last-write timestamp.',
   submit_calls=submit,remaining_seconds_at_last_submit_call=480-last['call_observed_seconds'] if last else None,
   remaining_seconds_after_last_submit_response=480-last['response_observed_seconds'] if last and last['response_observed_seconds'] is not None else None,
   charged_tools=row['charged_tools'],attempted_tools=row['metrics']['attempted_calls'],errors=errors,identical_command_repeats=repeats,
   git_diff_calls=[c for c in commands if re.search(r'\bgit\s+diff\b',c['args'].get('command',''))],
   command_calls=commands,tool_calls=ordered,first_effective_target_test_seconds=None,last_effective_target_verification_seconds=None,
   effective_test_status='REQUIRES_MANUAL_TRACE_REVIEW',agent_seconds=row['agent_seconds']))
doc=dict(archive_sha256=hashlib.sha256(Z.read_bytes()).hexdigest(),clock='Relative to each recorded agent_started monotonic time; ADK call/response observation times include observer latency.',sessions=result)
(OUT/'R2_BEHAVIOR_METRICS.json').write_text(json.dumps(doc,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
print(json.dumps([dict(index=x['index'],get_status=x['get_status_calls'],errors=len(x['errors']),submit_remaining=x['remaining_seconds_at_last_submit_call'],git_diff=len(x['git_diff_calls']),last_edit=(x['last_observed_successful_production_edit_call'] or {}).get('response_observed_seconds')) for x in result],indent=2))
