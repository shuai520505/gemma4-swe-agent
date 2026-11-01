"""Build only after real CPU receipts pass; this file does not dispatch."""
import base64,hashlib,json,sys,zipfile
from pathlib import Path
from datetime import datetime,timezone
D=Path(__file__).resolve().parent;ROOT=D.parents[1]
sha=lambda b:hashlib.sha256(b).hexdigest()
evidence=Path(sys.argv[1]).resolve()
summary=json.loads((evidence/'CPU_FINAL_SUMMARY.json').read_bytes())
assert summary['status']=='PASS' and summary['plumbing_replay']['status']=='PASS_PLUMBING_ONLY'
approved=json.loads((D/'APPROVED_EVALUATION_AMENDMENT.json').read_bytes())
assert approved['status']=='USER_APPROVED_BEFORE_REAL_MODEL_REQUESTS'
assert approved['original_proposal_sha256']==sha((D/'PENDING_EVALUATION_AMENDMENT.json').read_bytes())
metadata_files=('CPU_FINAL_SUMMARY.json','RUNTIME_OVERLAY_IDENTITIES.json','TASK_RUNTIME_311_IDENTITIES.json','SDK_SNAPSHOT_IDENTITIES.json','SOURCE_TREE_VERIFICATION.json')
expected={n:sha((evidence/n).read_bytes()) for n in metadata_files}
cpu_archive=D/'cpu-final-download/r2a-final-cpu-overlay.zip'
assert cpu_archive.is_file()
cpu_archive_sha=sha(cpu_archive.read_bytes())
overlays=json.loads((evidence/'RUNTIME_OVERLAY_IDENTITIES.json').read_bytes())
for n,h in overlays.items():assert sha((D/n).read_bytes())==h,('CPU-tested overlay differs',n)
fixed={n:sha((D/n).read_bytes()) for n in ('EXECUTION_PLAN.json','TASK_IDENTITY_LOCK.json','ISSUES.agent.json','TRUSTED_TEST_SPEC.private.json','APPROVED_EVALUATION_AMENDMENT.json')}
with zipfile.ZipFile(cpu_archive) as z:
 assert z.testzip() is None
 for n,h in fixed.items():assert sha(z.read('study/'+n))==h,('CPU-tested fixed input changed',n)
 for n,h in overlays.items():assert sha(z.read('study/'+n))==h,('CPU-tested module bytes differ',n)
receipt=dict(recorded_at_utc=datetime.now(timezone.utc).isoformat(),human_GPU_authorization='那就继续完成这个任务吧，可以在kaggle CIL上运行CPU和GPU进行实验',human_evaluation_decision='同意透明修订评估指标后继续实验',scope='One eight-session frozen R2/A study; four actual L4, 18000s maximum; no retry and no competition submission',candidate_sha256=json.loads((D/'EXECUTION_PLAN.json').read_bytes())['candidate_sha256'],CPU_receipts=expected,input_sha256=fixed,model_source='google/gemma-4/Other/gemma-4-31b-it-qat-w4a16-ct/2',Agent_limits=dict(seconds=480,charged_tools=28,turns=80,command_seconds=240),maximum_dispatches=1,retry_forbidden=True,competition_submission_authorized=False)
folder=D/'gpu-notebook';folder.mkdir(exist_ok=True)
(folder/'GPU_AUTHORIZATION.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
auth_raw=(folder/'GPU_AUTHORIZATION.json').read_bytes()
old=(ROOT/'work/gemma-r12-01/authorized-gpu-02/study.ipynb').read_bytes()
code="""import os,sys,json,hashlib,zipfile,subprocess,shutil,time,traceback,base64,textwrap
from pathlib import Path
SESSION_STARTED=time.monotonic()
RUN_DIR=Path('/kaggle/working/r2a-real-gpu-01');RUN_DIR.mkdir(exist_ok=False)
RESULT=dict(status='STARTED',GPU_dispatch_limit=1,model_requests_outside_sessions=0)
"""
code+='OLD=json.loads(base64.b64decode('+repr(base64.b64encode(old).decode())+'))\nEXPECTED_CPU='+repr(expected)+'\nCPU_ARCHIVE_SHA='+repr(cpu_archive_sha)+'\nFIXED='+repr(fixed)+'\nAUTH='+repr(base64.b64encode(auth_raw).decode())+'\nAUTH_SHA='+repr(sha(auth_raw))+'\n'
code+='''try:
 # Allocation observation precedes all SDK installs, model loads and requests.
 allocation=dict(status='GPU_ALLOCATION_FAILED',phase='pre_model_allocation',model_loaded_at_observation=False,model_requests_at_observation=0)
 try:
  for name,args in [('nvidia_smi_L',['nvidia-smi','-L']),('name_memory',['nvidia-smi','--query-gpu=name,memory.total','--format=csv,noheader'])]:
   p=subprocess.run(args,capture_output=True,text=True,timeout=30)
   allocation[name]=dict(exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr)
   assert p.returncode==0
  import torch
  allocation['torch_count']=torch.cuda.device_count()
  allocation['torch_devices']=[dict(name=torch.cuda.get_device_name(i),memory_bytes=torch.cuda.get_device_properties(i).total_memory) for i in range(torch.cuda.device_count())]
  lines=allocation['name_memory']['stdout'].strip().splitlines()
  import re
  assert len(lines)==4 and all(line.split(',')[0].strip()=='NVIDIA L4' and re.search(r',\s*[1-9][0-9]*\s*MiB',line) for line in lines)
  assert len([line for line in allocation['nvidia_smi_L']['stdout'].splitlines() if line.startswith('GPU ')])==4
  assert allocation['torch_count']==4 and all(d['name']=='NVIDIA L4' and d['memory_bytes']>0 for d in allocation['torch_devices'])
  for i in range(4):
   with torch.cuda.device(i):
    probe=torch.empty(1,device='cuda');torch.cuda.synchronize();del probe
  allocation['status']='GPU_ALLOCATION_CONFIRMED'
 except BaseException as e:allocation.update(error_type=type(e).__name__,reason=str(e))
 (RUN_DIR/'GPU_ALLOCATION.json').write_text(json.dumps(allocation,indent=2))
 (RUN_DIR/allocation['status']).write_text(allocation['status']+'\\n')
 assert allocation['status']=='GPU_ALLOCATION_CONFIRMED','GPU_ALLOCATION_FAILED: no model load or requests'
 raw=base64.b64decode(AUTH);assert hashlib.sha256(raw).hexdigest()==AUTH_SHA
 (RUN_DIR/'GPU_AUTHORIZATION.json').write_bytes(raw)
 first=OLD['cells'][0]['source'];second=OLD['cells'][1]['source']
 actual_started=SESSION_STARTED
 exec(compile(first[:first.index("guard['require_authorization']")],'accepted-bootstrap-definitions','exec'),globals())
 SESSION_STARTED=actual_started
 extension=RUN_DIR/'extension';extension.mkdir()
 for name,raw in BOOTSTRAP_FILES.items():(extension/name).write_bytes(raw)
 sys.path.insert(0,str(extension))
 exec(compile(first[first.index("SOURCE=RUN_DIR/'source'"):],'accepted-source-materialization','exec'),globals())
 install=textwrap.dedent(second[second.index(' import glob'):second.index(" assert allocation['status']")])
 exec(compile(install,'accepted-pinned-offline-sdk-install','exec'),globals())
 # The legacy bootstrap's historical authorization is never invoked. The
 # current study has its own validated receipt and one-shot dispatch claim.
 (extension/'GPU_AUTHORIZATION.json').write_bytes(base64.b64decode(AUTH))
 archives=list(Path('/kaggle/input').rglob('r2a-final-cpu-overlay.zip'));assert len(archives)==1
 assert hashlib.sha256(archives[0].read_bytes()).hexdigest()==CPU_ARCHIVE_SHA
 parent=RUN_DIR/'CPU_evidence';parent.mkdir()
 with zipfile.ZipFile(archives[0]) as z:
  assert z.testzip() is None and all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in z.namelist())
  z.extractall(parent)
  for info in z.infolist():
   if not info.is_dir():(parent/info.filename).chmod((info.external_attr>>16)&0o777 or 0o644)
 for n,h in EXPECTED_CPU.items():assert hashlib.sha256((parent/n).read_bytes()).hexdigest()==h,n
 summary=json.loads((parent/'CPU_FINAL_SUMMARY.json').read_bytes());assert summary['status']=='PASS'
 study=RUN_DIR/'study';shutil.move(str(parent/'study'),study)
 for n,h in FIXED.items():assert hashlib.sha256((study/n).read_bytes()).hexdigest()==h,n
 for n,h in json.loads((parent/'RUNTIME_OVERLAY_IDENTITIES.json').read_bytes()).items():assert hashlib.sha256((study/n).read_bytes()).hexdigest()==h,n
 for n,h in json.loads((parent/'TASK_RUNTIME_311_IDENTITIES.json').read_bytes())['files'].items():assert hashlib.sha256((study/n).read_bytes()).hexdigest()==h,n
 for row in json.loads((parent/'SDK_SNAPSHOT_IDENTITIES.json').read_bytes()):assert hashlib.sha256((study/'assets/snapshots'/(row['task']+'.tgz')).read_bytes()).hexdigest()==row['SDK_snapshot_sha256']
 plan=json.loads((study/'EXECUTION_PLAN.json').read_bytes())
 for n,h in plan['candidate_sha256'].items():assert hashlib.sha256((study/'candidates'/(n+'.zip')).read_bytes()).hexdigest()==h
 running=dict(status='ACTUAL_ALLOCATION_AND_CPU_INPUTS_CONFIRMED',authorization_sha256=AUTH_SHA,allocation_sha256=hashlib.sha256((RUN_DIR/'GPU_ALLOCATION.json').read_bytes()).hexdigest(),original_execution_plan_sha256=FIXED['EXECUTION_PLAN.json'],approved_evaluation_sha256=FIXED['APPROVED_EVALUATION_AMENDMENT.json'],input_sha256=FIXED,CPU_evidence=EXPECTED_CPU,candidate_sha256=plan['candidate_sha256'],session_order=plan['sessions'],window_seconds=18000,original_manifest_unchanged=True)
 (RUN_DIR/'ONE_TIME_RUN_MANIFEST.json').write_text(json.dumps(running,indent=2))
 os.environ['PYTHONPATH']=str(study)+os.pathsep+str(extension)+os.pathsep+str(SOURCE)
 from harness_v2.supervisor import supervise
 remaining=18000-(time.monotonic()-SESSION_STARTED)-900
 assert remaining>=1680*8,'Insufficient full eight-session lifecycle reserve'
 outcome=supervise([sys.executable,'-m','r2a_coordinator',str(RUN_DIR/'execution'),str(SESSION_STARTED)],RUN_DIR/'execution',outer_seconds=remaining,stage_caps=dict(prepare_agent=2400,load_model=1300,cleanup=180),cwd=SOURCE)
 (RUN_DIR/'NOTEBOOK_SUPERVISOR.json').write_text(json.dumps(outcome,indent=2))
 RESULT.update(status='EXECUTION_TERMINAL',supervisor=outcome)
except BaseException as e:
 RESULT.update(status='ALLOCATION_OR_INFRASTRUCTURE_STOP',error_type=type(e).__name__,reason=str(e),traceback=traceback.format_exc())
finally:
 try:
  if 'extension' in globals():
   from r12_authorized_dispatch import recover_owned
   (RUN_DIR/'OWNED_ROOT_RECOVERY.json').write_text(json.dumps(recover_owned(RUN_DIR/'execution'),indent=2))
 except BaseException as e:RESULT['recovery_error']=str(e)
 RESULT['first_cell_elapsed_seconds']=time.monotonic()-SESSION_STARTED
 (RUN_DIR/'NOTEBOOK_FINAL_STATUS.json').write_text(json.dumps(RESULT,indent=2))
 archive=shutil.make_archive(str(RUN_DIR),'zip',RUN_DIR)
 assert RUN_DIR.parent==Path('/kaggle/working') and RUN_DIR.name=='r2a-real-gpu-01'
 shutil.rmtree(RUN_DIR)
 print('R2A_GPU_TERMINAL',json.dumps(RESULT),flush=True)
 print('R2A_GPU_ARCHIVE',archive,flush=True)
'''
compile(code,'gpu-notebook','exec')
nb=dict(nbformat=4,nbformat_minor=5,metadata=dict(kernelspec=dict(name='python3',language='python',display_name='Python 3')),cells=[dict(cell_type='code',execution_count=None,id='r2arealgpu',metadata={},outputs=[],source=code)])
(folder/'study.ipynb').write_text(json.dumps(nb,indent=1)+'\n')
meta=json.loads((ROOT/'work/gemma-r12-01/authorized-gpu-02/kernel-metadata.json').read_bytes())
meta.update(id='wudangdexiaodoashi/r2a-real-gpu-01',title='R2A Frozen Paired Real GPU 01',enable_gpu=True,enable_internet=False,machine_shape='NvidiaL4')
meta['kernel_sources'].append('wudangdexiaodoashi/r2a-final-cpu-overlay-01')
(folder/'kernel-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
build=dict(notebook_sha256=sha((folder/'study.ipynb').read_bytes()),metadata_sha256=sha((folder/'kernel-metadata.json').read_bytes()),authorization_sha256=sha(auth_raw),CPU_evidence=expected,CPU_archive_sha256=cpu_archive_sha,maximum_dispatches=1,maximum_seconds=18000,required_quota_seconds=73200)
(folder/'BUILD.json').write_text(json.dumps(build,indent=2)+'\n')
print(json.dumps(build))
