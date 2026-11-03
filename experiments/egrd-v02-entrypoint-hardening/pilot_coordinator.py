"""One bounded two-task smoke for one explicitly confirmed model; no automatic dispatch."""
import asyncio,hashlib,importlib.metadata as md,json,os,sys,time,uuid
from pathlib import Path
import psutil,torch
from dataclasses import asdict
from adk_submission import VllmConfig,VllmServer,discover_adapters
from s1.experiments.e3_localize_smoke_03.idle import require_idle
from s1.verifier_v3.backend_logs import capture_logs
from r2a_runtime import HERE
from supervision import supervise
from result_contract import dump,sha,seal
from model_selection import decide
D=Path(__file__).resolve().parent

def alive(p):
 try:return p.is_running() and p.status()!=psutil.STATUS_ZOMBIE
 except psutil.NoSuchProcess:return False

async def run(out,started,model,confirmation_sha256):
 out=Path(out);out.mkdir(parents=True,exist_ok=True);sid=uuid.uuid4().hex
 assert model in ['12b','31b'] and confirmation_sha256
 plan=json.loads((D/'SMOKE_TASK_LOCK.json').read_bytes());models=json.loads((D/'MODEL_CONFIGURATIONS.json').read_bytes());cfg=models[model]
 rows=json.loads((D/'ISSUES.agent.json').read_bytes());issues={r['instance_id']:r for r in rows}
 versions={n:md.version(n) for n in ['torch','vllm','swegemma','adk-submission','google-adk']}
 expected=json.loads((D/'RUNTIME_LOCK.json').read_bytes());assert versions==expected['versions'],'Runtime version changed'
 devices=[dict(name=torch.cuda.get_device_name(i),memory=torch.cuda.get_device_properties(i).total_memory) for i in range(torch.cuda.device_count())]
 assert len(devices)==4 and all(r['name']=='NVIDIA L4' and r['memory']>0 for r in devices)
 dump(out/'ACTUAL_GPU.json',dict(devices=devices,versions=versions,CUDA=torch.version.cuda))
 mount=Path('/kaggle/input/models/google/gemma-4/other')/cfg['alias']/'2'
 observed={p.relative_to(mount).as_posix():sha(p) for p in mount.rglob('*') if p.is_file()}
 dump(out/'MODEL_IDENTITY.json',dict(alias=cfg['alias'],files=observed));assert observed==cfg['expected_files']
 competition=next((p for p in [Path('/kaggle/input/competitions/gemma-4-developer-agent'),Path('/kaggle/input/gemma-4-developer-agent')] if (p/'tasks.jsonl').is_file()),None)
 assert competition and sha(competition/'tasks.jsonl')==plan['pool_sha256'],'Public task pool identity mismatch'
 os.environ.update(VLLM_WORKER_MULTIPROC_METHOD='spawn',VLLM_NO_USAGE_STATS='1',VLLM_ENGINE_READY_TIMEOUT_S='1200',VLLM_MEMORY_PROFILER_ESTIMATE_CUDAGRAPHS='1',NCCL_DEBUG='WARN',LOCAL_API_KEY='EMPTY',OPENAI_API_KEY='EMPTY')
 empty=out/'no-adapters';empty.mkdir();extra=tuple(cfg['extra_args'])+('--no-enable-prefix-caching',)
 assert model!='31b' or cfg['extra_args']==[]
 vcfg=VllmConfig(model=str(mount),host='127.0.0.1',port=8000,max_model_len=32768,dtype='bfloat16',gpu_memory_utilization=.9,tensor_parallel_size=4,enable_auto_tool_choice=True,tool_call_parser='gemma4',reasoning_parser='gemma4',scheduler_reserve_full_isl=False,enable_lora=False,startup_timeout=1200,extra_args=extra)
 server=VllmServer(vcfg,adapter_manifest=discover_adapters(str(empty)));known=[];children=[];records=[];stop=None;errors=[]
 try:
  assert 18000-(time.monotonic()-started)>=4500,'Insufficient full smoke/load/evaluation/archive reserve'
  dump(out/'SERVER_CONFIG.json',dict(config=asdict(vcfg),command=server.build_cmd()));before=time.monotonic();server.start();dump(out/'MODEL_LOAD.json',dict(seconds=time.monotonic()-before))
  known=[psutil.Process(server.process.pid)]+psutil.Process(server.process.pid).children(recursive=True)
  for index,task in enumerate(plan['tasks'],1):
   await require_idle(server.base_url,out/f'idle-before-{index}',seconds=60)
   snapshot=competition/'snapshots'/task['snapshot_file'];assert sha(snapshot)==task['official_snapshot_sha256']
   issue=issues[task['instance_id']];assert hashlib.sha256(issue['problem_statement'].encode()).hexdigest()==task['issue_sha256']
   spec=dict(session_id=f'{sid}-{index}',candidate='B' if model=='12b' else 'D',model_path=str(mount),model_alias=cfg['alias'],real_Gemma=True,authorized_GPU_pilot=True,human_confirmation_sha256=confirmation_sha256,binding=dict(issue=issue,snapshot=str(snapshot),wheels=str(HERE/'assets/wheels'),agent_tasks=str(D/'ISSUES.agent.json'),public_tasks=str(competition/'tasks.jsonl'),test_patch_sha256=task['public_evaluator_test_patch_sha256']))
   specfile=out/'specs'/f'{index}.json';dump(specfile,spec);directory=out/'sessions'/f'{index:02d}_{task["instance_id"]}'
   outcome=await asyncio.to_thread(supervise,[sys.executable,'-m','pilot_worker',str(specfile),str(directory)],directory,role='session',outer_seconds=1200,stage_caps=dict(prepare_agent=240,agent=345,save_patch=60,verification=600,persist=60,cleanup=120),cwd=D)
   records.append(dict(task=task['instance_id'],outcome=outcome));children.append(dict(receipt=(directory/'SUPERVISOR_RESULT.json').relative_to(out).as_posix(),sha256=sha(directory/'SUPERVISOR_RESULT.json')))
   dump(out/'SMOKE_PROGRESS.json',dict(records=records,not_run=[r['instance_id'] for r in plan['tasks'][index:]]))
   if not outcome['allow_next_run']:stop=outcome['classification'];break
   await require_idle(server.base_url,out/f'idle-after-{index}',seconds=60)
 except BaseException as exc:
  import traceback
  stop=dict(type=type(exc).__name__,reason=str(exc),traceback=traceback.format_exc())
 finally:
  try:
   capture_logs(server,out/'backend_logs',phase='before-stop');server.stop();capture_logs(server,out/'backend_logs',phase='after-stop');psutil.wait_procs(known,timeout=10)
  except BaseException as exc:errors.append(dict(type=type(exc).__name__,reason=str(exc)))
  live=[p.pid for p in known if alive(p)]
  trusted=all(r['outcome']['allow_next_run'] for r in records);clean=not errors and not live and all(r['outcome']['cleanup_complete'] for r in records)
  diagnostic=[]
  for index,r in enumerate(records,1):
   directory=out/'sessions'/f'{index:02d}_{r["task"]}'
   result=json.loads((directory/'SESSION_RESULT.json').read_bytes()) if (directory/'SESSION_RESULT.json').exists() else {}
   act=result.get('activation') or {};tool_ok=all((act.get(n) or {}).get('status')!='TOOL_NOT_AVAILABLE' for n in ['load_skill','run_skill_script']) and bool(act)
   fault='MODEL_DID_NOT_CALL' if tool_ok and any((act.get(n) or {}).get('status')=='MODEL_DID_NOT_CALL' for n in ['load_skill','run_skill_script']) else None
   diagnostic.append(dict(task_id=r['task'],infrastructure_ok=r['outcome']['allow_next_run'],tools_available=tool_ok,activation=bool(act.get('activated') and act.get('state_issue_hash_matches')),evidence_records=act.get('evidence_records'),model_failure=fault,native_resolved=result.get('native_resolved')))
  decision=decide(diagnostic,model) if diagnostic else 'STOP_INFRASTRUCTURE'
  complete=len(records)==len(plan['tasks']) and stop is None
  row=dict(schema='EGRD_AGGREGATE_V2',session_id=sid,model=model,planned_sessions=len(plan['tasks']),complete=complete,children_trusted=trusted,children=children,records=records,stop_reason=stop,model_decision=decision,diagnostic=diagnostic,not_run=[r['instance_id'] for r in plan['tasks'][len(records):]],automatic_GPU_dispatch=False,engineering_pass=complete and all(r['activation'] and (r['evidence_records'] or 0)>0 for r in diagnostic))
  cleanup=dict(schema='EGRD_CLEANUP_V2',session_id=sid,complete=clean,records=records,model_processes_still_live=live,errors=errors)
  seal(out,row,cleanup,0,role='aggregate')
if __name__=='__main__':asyncio.run(run(sys.argv[1],float(sys.argv[2]),sys.argv[3],sys.argv[4]))
