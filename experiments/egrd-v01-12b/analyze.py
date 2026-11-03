"""Summarize observed pilot receipts without imputing missing semantic facts."""
import collections,hashlib,json,statistics,zipfile
from pathlib import Path
D=Path(__file__).resolve().parent

def summarize_session(z,prefix,result):
 names=set(z.namelist())
 def read(n):return json.loads(z.read(prefix+n)) if prefix+n in names else None
 def lines(n):return [json.loads(x) for x in z.read(prefix+n).decode().splitlines() if x.strip()] if prefix+n in names else []
 events=lines('adk_events.jsonl');actions=[];responses={};counts=collections.Counter()
 for row in events:
  for part in row.get('event',{}).get('content',{}).get('parts',[]):
   if 'function_call' in part:
    call=part['function_call'];counts[call['name']]+=1;actions.append(dict(name=call['name'],id=call.get('id'),args=call.get('args'),time=row['recorded_monotonic']))
   if 'function_response' in part:
    resp=part['function_response'];responses[resp.get('id')]=dict(time=row['recorded_monotonic'],**resp)
 stages=lines('events.jsonl');start=next((r['recorded_monotonic'] for r in stages if r.get('kind')=='stage' and r.get('stage')=='agent' and r.get('agent_started') is True),None)
 # First model request is a separate observable origin when no Agent stage timestamp is available.
 transport=lines('model_transport/http_lifecycle.jsonl');first_request=next((r['recorded_monotonic'] for r in transport if r['kind']=='request_sent'),None)
 origin=start if start is not None else first_request
 for a in actions:
  a['seconds_from_origin']=a['time']-origin if origin is not None else None
  resp=responses.get(a['id']);a['response_status']=resp.get('response',{}).get('status') if resp else None
  a['tool_elapsed_seconds']=resp['time']-a['time'] if resp else None
 state=read('EGRD_STATE.json');patches=[n for n in names if n.startswith(prefix) and n[len(prefix):] in ['submitted.patch','fallback.patch']]
 errors=[a for a in actions if a['response_status'] in ['error','warning']]
 edits=[a for a in actions if a['name'] in ['edit_file','write_file'] and a['response_status']=='ok']
 http_times=[r['elapsed_seconds'] for r in transport if r['kind']=='terminal_status' and r.get('status')=='response_received' and r.get('elapsed_seconds') is not None]
 return dict(result=result,origin_kind='SDK_AGENT_STARTED_STAGE' if start is not None else 'FIRST_HTTP_REQUEST_NOT_SESSION_START',origin_monotonic=origin,ADK_tool_calls=dict(counts),ADK_total_tool_calls=sum(counts.values()),actions=actions,tool_warnings_or_errors=errors,first_successful_edit_tool_seconds=edits[0]['seconds_from_origin'] if edits else None,first_relevant_production_edit_seconds=None,causal_localization_correct=None,issue_alignment_semantic=None,patch_correct=None,patches=[dict(path=n,sha256=hashlib.sha256(z.read(n)).hexdigest(),bytes=len(z.read(n))) for n in patches],EGRD=None if state is None else dict(phase=state.get('phase'),evidence_records=len(state.get('evidence',[])),evidence_types=dict(collections.Counter(e.get('type') for e in state.get('evidence',[]))),hypothesis_recorded=bool(state.get('cause')),intent_recorded=bool(state.get('patch_intent')),revisions=state.get('revisions'),relayed_issue_sha256=state.get('contract',{}).get('original_sha256'),model_id=state.get('model_id')),HTTP_response_elapsed_seconds=http_times,HTTP_elapsed_mean=statistics.mean(http_times) if http_times else None,HTTP_elapsed_scope='Observed transport latency includes backend/prefill/decode/wait; not isolated thinking time')

def main():
 archive=D/'gpu-output/egrd-v01-12b-pilot01.zip'
 with zipfile.ZipFile(archive) as z:
  assert z.testzip() is None;names=set(z.namelist())
  pilot=json.loads(z.read('execution/PILOT_RESULTS.json')) if 'execution/PILOT_RESULTS.json' in names else dict(records=[],not_run=json.loads((D/'TASK_IDENTITY_MANIFEST.json').read_bytes())['sessions'],stop='NO_COORDINATOR_RESULT')
  rows=[]
  for record in pilot['records']:
   prefix=f"execution/sessions/{record['index']:02d}_{record['candidate']}_{record['task']}/"
   row=summarize_session(z,prefix,record['result']);row.update(index=record['index'],task=record['task'],candidate=record['candidate'],model=record['model']);rows.append(row)
  index=[dict(path=n,bytes=len(z.read(n)),sha256=hashlib.sha256(z.read(n)).hexdigest()) for n in z.namelist() if not n.endswith('/')]
  models={size:{n:json.loads(z.read('execution/'+size+'/'+n+'.json')) for n in ['MODEL_IDENTITY','MODEL_LOAD','SERVER_CONFIG','SERVER_CLEANUP'] if 'execution/'+size+'/'+n+'.json' in names} for size in ['12b','31b']}
  summary=dict(scope='REAL_GPU_OBSERVATION only for recovered actual sessions; public development SDK Native, not hidden competition score',archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),pilot=pilot,sessions=rows,models=models,semantic_review='SEPARATE_PENDING',official_hidden_native_resolved=None,S0_superiority=None,corrected_current_script_real_model_evaluation='NOT_RUN')
 (D/'PILOT_METRICS.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
 (D/'PILOT_EVIDENCE_INDEX.json').write_text(json.dumps(dict(archive_sha256=summary['archive_sha256'],files=index),indent=2)+'\n')
 print(json.dumps(dict(sessions=len(rows),not_run=len(pilot['not_run']),stop=pilot.get('stop'))))
if __name__=='__main__':main()
