"""Fresh official SDK session, passive exact deadline, separate native verification."""
import asyncio,hashlib,json,sys,time,uuid
from pathlib import Path
import runtime_adapter
runtime_adapter.install()
from hardened_runtime import SubprocessManager,DurableContext as ParentContext
from harness_v2.evidence import Journal
from swegemma.models import Task
from swegemma.harness.agent_runner import run_agent_sandbox
from s1.infrastructure_recovery.wire import observe_http,audit_requests
from r2a_runtime import context_config,HERE
from timing import observe_deadline,deadline_evidence
from result_contract import dump,sha,seal
RUNTIME_LOCK=json.loads((Path(__file__).resolve().parent/'RUNTIME_LOCK.json').read_bytes())
assert sha(Path(run_agent_sandbox.__code__.co_filename))==RUNTIME_LOCK['SDK_runner_sha256'],'SDK runner changed; deadline observation requires revalidation'
from activation import audit as activation_audit

class Context(ParentContext):
 def stop_agent_session(self):
  super().stop_agent_session();box=self.docker.sandboxes.get(self.container_id)
  if box:
   p=box['root']/'tmp/egrd-v01/state.json'
   if p.is_file() and not p.is_symlink() and p.resolve().is_relative_to(box['root'].resolve()) and p.stat().st_size<=8*1024*1024:dump(self.journal.directory/'EGRD_STATE.json',json.loads(p.read_bytes()))

def read_events(path):return [json.loads(x) for x in path.read_text(encoding='utf8').splitlines() if x.strip()] if path.exists() else []

def manager_clean(manager):return not manager.sandboxes and all(not Path(e['lease']).exists() for e in manager.entries)

async def native_evaluate(spec,patch,out,cfg):
 # Original public evaluator test_patch is loaded only after the Agent has ended.
 from swegemma.harness.verification import verify_task
 issue=spec['binding']['issue'];rows=[json.loads(s) for s in Path(spec['binding']['public_tasks']).read_text(encoding='utf8').splitlines() if s.strip()]
 original=next(r for r in rows if r['instance_id']==issue['instance_id'])
 assert hashlib.sha256(original['test_patch'].encode()).hexdigest()==spec['binding']['test_patch_sha256']
 task=Task(**issue,test_patch=original['test_patch']) # Never access reference production patch or hints.
 mgr=SubprocessManager(journal=Journal(out),base_dir=out/'roots',task_wheels=Path(spec['binding']['wheels']),timeout_seconds=120,project_version=spec['binding'].get('version'),task_repo=issue['repo'])
 try:
  result=await verify_task(mgr,cfg,task,Path(spec['binding']['snapshot']),agent_patch=patch,start_time=time.perf_counter())
  row=result.model_dump(mode='json',exclude={'trace'});dump(out/'NATIVE_RESULT.json',row)
  dump(out/'VERIFICATION_SOURCE_GUARD.json',getattr(mgr,'verification_guard',None));return row
 finally:
  mgr.cleanup_all();dump(out/'NATIVE_COMMANDS.json',mgr.command_records)
  dump(out/'CLEANUP.json',dict(complete=manager_clean(mgr),records=mgr.cleanup_records))

async def run(spec,out):
 start=time.monotonic();out=Path(out);out.mkdir(parents=True,exist_ok=True);sid=spec.get('session_id') or uuid.uuid4().hex
 issue=spec['binding']['issue'];journal=Journal(out);simulation=spec.get('CPU_simulation') is True
 if simulation:
  import torch
  assert torch.cuda.device_count()==0 and spec['model_path']=='SIMULATED_CPU_NO_MODEL' and not spec['real_Gemma']
 else:assert spec['real_Gemma'] and spec.get('authorized_GPU_pilot') and spec.get('human_confirmation_sha256')
 cfg,agent=context_config(spec['candidate'],out,spec['binding']['snapshot'],Path(spec['binding']['agent_tasks']),Path(spec['binding']['wheels']),spec['model_path'])
 assert cfg.harness.verification_timeout_seconds==300
 dump(out/'CONFIGURATION.json',dict(candidate=spec['candidate'],model_alias=spec['model_alias'],model_path=spec['model_path'],prompt_sha256=hashlib.sha256(agent.instruction.encode()).hexdigest(),generation=agent.generate_content_config.model_dump(mode='json',exclude_none=True),Agent_seconds=300,command_seconds=120,tool_calls=60,turns=80,execution_mode='PROMPT_ENFORCED_OPTIONAL_EXECUTION'))
 manager=SubprocessManager(journal=journal,base_dir=out/'roots',task_wheels=Path(spec['binding']['wheels']),timeout_seconds=120,project_version=spec['binding'].get('version'))
 task=Task(**issue);assert not task.patch and not task.test_patch and not task.hints_text
 ctx=Context(journal=journal,docker_manager=manager,task=task,budget=cfg.budget,harness=cfg.harness);manager.context=ctx
 row=dict(schema='EGRD_SESSION_V2',session_id=sid,task_id=task.instance_id,candidate=spec['candidate'],model_alias=spec['model_alias'],model_transport='CPU_SCRIPTED_NOT_REPAIR_EVIDENCE' if simulation else 'REAL_GEMMA',failure_classification='INFRASTRUCTURE_FAILURE',native_resolved=None,native_result_path='trusted/NATIVE_RESULT.json',native_result_sha256=None)
 exit_code=0;failure=None;native_clean=True;native_started=False
 try:
  with observe_deadline(run_agent_sandbox,out/'SDK_DEADLINE.json',300) as observation:
   ctx.deadline_observation=observation
   with observe_http(out/'model_transport'):patch,error,trace=await run_agent_sandbox(manager,cfg,task,Path(spec['binding']['snapshot']),context=ctx)
  journal.stage('save_patch');dump(out/'native_trace.json',trace.to_dict() if trace else {})
  label='submitted' if ctx.patch_submitted else 'fallback';(out/(label+'.patch')).write_text(patch,encoding='utf8')
  manager.cleanup_all();clean=manager_clean(manager)
  http=audit_requests(out/'model_transport',deadline_evidence=deadline_evidence(observation.receipt,error,clean))
  events=read_events(out/'adk_events.jsonl');wire=read_events(out/'model_transport/http_wire.jsonl')
  first=next((r['body'] for r in wire if r['kind']=='http_request'),{})
  available=[t['function']['name'] for t in first.get('tools',[])]
  state=json.loads((out/'EGRD_STATE.json').read_bytes()) if (out/'EGRD_STATE.json').is_file() else None
  act=activation_audit(events,available,hashlib.sha256(issue['problem_statement'].encode()).hexdigest(),state);dump(out/'ACTIVATION_AUDIT.json',act)
  actual_deadline=deadline_evidence(observation.receipt,error,clean)['official_agent_deadline']
  classification='AGENT_TIMEOUT' if actual_deadline else 'MODEL_BACKEND_ERROR' if error else 'NO_PATCH' if not patch else 'AGENT_COMPLETED'
  if (not http['passed'] and classification!='MODEL_BACKEND_ERROR') or (act['activated'] and not act['state_issue_hash_matches']):classification='EVIDENCE_INCOMPLETE'
  if ctx.stop_receipt().get('stopped'):classification='INFRASTRUCTURE_FAILURE'
  row.update(failure_classification=classification,agent_error=error,SDK_agent_elapsed_seconds=ctx.agent_elapsed_seconds,raw_late_counter_elapsed_seconds=ctx.agent_end_time-getattr(ctx,'raw_sdk_agent_start_time',ctx.agent_start_time) if ctx.agent_end_time else None,agent_timing=observation.receipt,charged_tools=ctx.tool_calls_used,SDK_llm_counter=ctx.llm_calls_used,patch_bytes=len(patch.encode()),patch_submitted=ctx.patch_submitted,patch_kind=label,http_audit=http,activation=act,activation_audit_sha256=sha(out/'ACTIVATION_AUDIT.json'),infrastructure_stop=ctx.stop_receipt())
  if classification in ['AGENT_COMPLETED','AGENT_TIMEOUT','NO_PATCH']:
   journal.stage('verification');native_started=True;native_clean=False;native=await native_evaluate(spec,patch,out/'trusted',cfg)
   row.update(native_result_sha256=sha(out/'trusted/NATIVE_RESULT.json'),native_resolved=native['resolved'])
  native_clean=json.loads((out/'trusted/CLEANUP.json').read_bytes()).get('complete') is True if (out/'trusted/CLEANUP.json').exists() else classification not in ['AGENT_COMPLETED','AGENT_TIMEOUT','NO_PATCH']
 except BaseException as exc:
  import traceback
  failure=exc;exit_code=1;row.update(failure_classification='INFRASTRUCTURE_FAILURE',exception=dict(type=type(exc).__name__,reason=str(exc),traceback=traceback.format_exc()))
 finally:
  cleanup_errors=[]
  if native_started:
   try:native_clean=json.loads((out/'trusted/CLEANUP.json').read_bytes()).get('complete') is True
   except (OSError,ValueError):native_clean=False
  try:manager.cleanup_all()
  except BaseException as exc:cleanup_errors.append(dict(type=type(exc).__name__,reason=str(exc)))
  clean=not cleanup_errors and manager_clean(manager) and native_clean
  cleanup=dict(schema='EGRD_CLEANUP_V2',session_id=sid,complete=clean,records=manager.cleanup_records,native_cleanup=native_clean,errors=cleanup_errors)
  row.update(worker_seconds=time.monotonic()-start,cleanup_status=clean)
  journal.stage('cleanup');seal(out,row,cleanup,exit_code)
 if failure:raise failure
if __name__=='__main__':asyncio.run(run(json.loads(Path(sys.argv[1]).read_bytes()),sys.argv[2]))
