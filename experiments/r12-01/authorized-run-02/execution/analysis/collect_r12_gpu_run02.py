"""Read-only recovery of real R12 results. Semantic review is required before any repair is validated."""
import hashlib,json,sys,zipfile
from pathlib import Path
WORK=Path(__file__).resolve().parent;ROOT=WORK/'gemma-r12-01/authorized-gpu-02';OUT=WORK.parent/'outputs/r12_gpu_run02'
OUT.mkdir(exist_ok=True)
original=json.loads((WORK.parent/'outputs/r12_final_gpu_readiness/GPU_DISPATCH_PACKAGE_MANIFEST.json').read_bytes())
sha=lambda raw:hashlib.sha256(raw).hexdigest()
write=lambda name,value:(OUT/name).write_bytes((json.dumps(value,indent=2,ensure_ascii=False)+'\n').encode())
archive=Path(sys.argv[1]);semantic_path=OUT/'INDEPENDENT_SEMANTIC_REVIEW.json'
semantic=json.loads(semantic_path.read_bytes()) if semantic_path.is_file() else {}
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 members=set(z.namelist());index=[]
 for info in z.infolist():
  if not info.is_dir():index.append(dict(path=info.filename,bytes=info.file_size,sha256=sha(z.read(info))))
 def read(name):
  return json.loads(z.read(name)) if name in members else None
 pair=read('execution/PAIR_RESULTS.json') or dict(records=[],not_run=[[s['instance_id'],s['candidate']] for s in original['sessions']])
 records=pair['records'];lookup={r['index']:r for r in records};rows=[];patches=[]
 for s in original['sessions']:
  i=s['index'];key=f"{i:02d}_{s['candidate']}_{s['instance_id']}";prefix='execution/sessions/'+key+'/'
  native=read(prefix+'SESSION_RESULT.json');agent=read(prefix+'AGENT_RESULT.json');metrics=read(prefix+'R12_METRICS.json');exception=read(prefix+'WORKER_EXCEPTION.json')
  retained=native or agent or {}
  record=lookup.get(i);review=semantic.get(str(i));patch_kind=(native or {}).get('patch_kind')
  attempted=record is not None or any(name.startswith(prefix) for name in members)
  patch_path=prefix+('submitted.patch' if retained.get('patch_submitted') else 'fallback.patch')
  patch=z.read(patch_path) if patch_path in members else None
  if patch:
   if retained:assert sha(patch)==retained['patch_sha256'] and len(patch)==retained['patch_bytes']
   dest=OUT/'private-patches'/f'{key}.patch';dest.parent.mkdir(exist_ok=True);dest.write_bytes(patch)
   patches.append(dict(index=i,file=str(dest),bytes=len(patch),sha256=sha(patch)))
  evaluation=(native or {}).get('evaluation') or {}
  error=str((native or {}).get('agent_error') or '')
  if not attempted:status='NOT_RUN'
  elif native is None:status='ENVIRONMENT_BLOCKED' if exception else 'UNKNOWN'
  elif any(word in error.lower() for word in ('contextwindow','context_length','contextbudget','contextcounting','litellm.','openaiexception')):status='CONTEXT_ERROR'
  elif patch is None:status='UNKNOWN'
  elif not patch:status='NO_PATCH'
  elif not native.get('evidence_complete') or not native.get('cleanup') or not ((record or {}).get('worker') or {}).get('allow_next_run'):status='PARTIAL_REPAIR'
  elif not all(evaluation.get(k) is True for k in ('check_unchanged','check_write_denied','source_unchanged_by_checks')):status='PARTIAL_REPAIR'
  elif not evaluation.get('positive_controls_passed'):status='ENVIRONMENT_BLOCKED'
  elif not evaluation.get('scoped_development_pass'):status='INVALID_REPAIR'
  elif review is None:status='PARTIAL_REPAIR'
  elif review.get('repair_approved') is True and review.get('valid_production_change') is True and review.get('issue_semantics_satisfied') is True:status='VALIDATED_REPAIR'
  else:status='INVALID_REPAIR'
  timeout=bool(native and not native.get('patch_submitted') and patch and 'timeout' in error.lower())
  wire_path=prefix+'model_transport/http_wire.jsonl'
  wire=[json.loads(line) for line in z.read(wire_path).splitlines()] if wire_path in members else None
  model_requests=[x for x in wire if x.get('kind')=='http_request'] if wire is not None else None
  rows.append(dict(index=i,instance_id=s['instance_id'],candidate=s['candidate'],status=status,
      agent_outcome='TIMEOUT_WITH_FALLBACK' if timeout else ('EXPLICIT_SUBMIT' if (native or {}).get('patch_submitted') else ('NO_EXPLICIT_SUBMIT' if native else 'NOT_RUN')),
      worker_started=attempted,PAIR_record_persisted=record is not None,session_result_saved=native is not None,model_transport=(native or {}).get('model_transport'),
      agent_error=(native or {}).get('agent_error'),worker_exception=exception,
      patch_bytes=len(patch) if patch is not None else None,patch_sha256=sha(patch) if patch else None,patch_submitted=(native or {}).get('patch_submitted'),patch_kind=patch_kind,
      agent_seconds=retained.get('agent_seconds'),worker_seconds=(native or {}).get('worker_seconds'),charged_tools=retained.get('charged_tools'),llm_calls=retained.get('llm_calls'),
      retained_agent_result_available=agent is not None,model_HTTP_requests=len(model_requests) if model_requests is not None else None,
      metrics=metrics,evaluation=evaluation,semantic_review=review,cleanup=(native or {}).get('cleanup'),supervisor=(record or {}).get('worker')))
 allocation=read('GPU_ALLOCATION.json');identity=read('execution/MODEL_IDENTITY.json');load=read('execution/MODEL_LOAD_COMPLETED.json')
 if identity:assert identity['files']==original['configuration']['model_files']
 source_original=z.read('extension/GPU_DISPATCH_PACKAGE_MANIFEST.original.json')
 assert sha(source_original)=='90593990ea2bacba29e94ab0941063f1d2e31063b6235739c744192fdc8739d2'
 assert read('extension/GPU_AUTHORIZATION.json')['run_id']=='R12_AUTHORIZED_GPU_RUN_02'
 summary=dict(run_id='R12_AUTHORIZED_GPU_RUN_02',real_experiment=True,archive_sha256=sha(archive.read_bytes()),archive_bytes=archive.stat().st_size,CRC_pass=True,
     allocation=allocation,model_files=identity,model_load=load,pair_summary=pair,stop=read('execution/STOP.json'),authorized_stop=read('AUTHORIZED_EXECUTION_STOP.json'),Notebook_exception=read('NOTEBOOK_EXCEPTION.json'),
     Notebook_supervisor=read('NOTEBOOK_SUPERVISOR.json'),server_cleanup=read('execution/SERVER_CLEANUP.json'),owned_root_recovery=read('OWNED_ROOT_RECOVERY.json'),owned_root_recovery_error=read('OWNED_ROOT_RECOVERY_ERROR.json'),
     sessions=rows,workers_started=sum(r['worker_started'] for r in rows),sessions_with_saved_result=sum(r['session_result_saved'] for r in rows),
     real_Gemma_sessions=sum(r['model_transport']=='REAL_GEMMA' and bool(r['model_HTTP_requests']) for r in rows),validated_repairs=sum(r['status']=='VALIDATED_REPAIR' for r in rows),
     independent_semantic_review_complete=all(r['semantic_review'] is not None for r in rows if r['patch_bytes']),
     candidate_results={c:dict(sessions_started=sum(r['worker_started'] for r in rows if r['candidate']==c),saved_results=sum(r['session_result_saved'] for r in rows if r['candidate']==c),validated_repairs=sum(r['status']=='VALIDATED_REPAIR' for r in rows if r['candidate']==c)) for c in ('BASELINE','R1','R2')},
     formal_submissions=0,R3_built=False,selective_reruns=0)
 write('R12_GPU_RESULTS.json',summary)
 write('R12_SESSION_EVIDENCE_INDEX.json',dict(run_id=summary['run_id'],archive_sha256=summary['archive_sha256'],sessions=[dict(index=r['index'],instance_id=r['instance_id'],candidate=r['candidate'],status=r['status'],prefix='execution/sessions/'+f"{r['index']:02d}_{r['candidate']}_{r['instance_id']}/",model_transport=r['model_transport']) for r in rows],members=index))
 write('PATCH_REVIEW_INPUTS.private.json',patches)
 print(json.dumps(dict(allocation=(allocation or {}).get('status'),workers_started=summary['workers_started'],saved_results=summary['sessions_with_saved_result'],real_Gemma_sessions=summary['real_Gemma_sessions'],patches_to_review=len(patches),stop=summary['stop'],statuses=[r['status'] for r in rows])))
