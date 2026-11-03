"""Build only after exact CPU worker/Skill proof and model mount identity."""
import base64,hashlib,json,zipfile
from pathlib import Path
D=Path(__file__).resolve().parent;ROOT=D.parents[1]
cpu=D/'cpu-output/egrd-v01-12b-cpu01.zip'
with zipfile.ZipFile(cpu) as z:
    assert z.testzip() is None
    proof=json.loads(z.read('CPU_SUMMARY.json'));assert proof['status']=='PASS' and len(proof['stages'])==4
    assert json.loads(z.read('worker/WORKER_CPU_ACCEPTANCE.json'))['status']=='PASS_PLUMBING_ONLY'
    model12=json.loads(z.read('MODEL_12B_MOUNT.json'));ids=json.loads(z.read('SOURCE_IDENTITIES.json'))
    for name in ['core.py','meer_verifier.py','skill_cli.py','runtime_adapter.py','pilot_worker.py','worker_cpu.py','PACKAGE_MANIFEST.json']:
        assert hashlib.sha256((D/name).read_bytes()).hexdigest()==ids[name],name
models=json.loads((D/'MODEL_CONFIGURATIONS.json').read_bytes());models['12b']['expected_files']=model12['files']
lock=json.loads((ROOT/'outputs/r12_redispatch/mount-mirror/source/gemma_pair/GPU_ENVIRONMENT_LOCK.json').read_bytes());models['31b']['expected_files']=lock['model_files']
(D/'MODEL_CONFIGURATIONS.json').write_text(json.dumps(models,indent=2)+'\n')
files={n:(D/n).read_bytes() for n in ['runtime_adapter.py','pilot_worker.py','pilot_coordinator.py','PACKAGE_MANIFEST.json','TASK_IDENTITY_MANIFEST.json','MODEL_CONFIGURATIONS.json']}
for n in ['hardened_runtime.py','stop_policy.py']:files[n]=(D.parent/'r2-infra-hardening-01'/n).read_bytes()
files.update({p.relative_to(D).as_posix():p.read_bytes() for p in (D/'packages').rglob('*') if p.is_file()})
files['CPU_PROOF.json']=json.dumps(dict(summary=proof,archive_sha256=hashlib.sha256(cpu.read_bytes()).hexdigest(),identities=ids),indent=2).encode()
auth=dict(scope='EGRD V0.1 Gemma12B three-development-task engineering pilot,31B extension only if pilot workflow and resource gates pass',human_request='Codex Master Task — EGRD V0.1 Implementation & Gemma 12B Evaluation; First run a small pilot of approximately 3–5 development tasks; Run D only if resources permit.',prior_general_GPU_authorization='授权你用GPU 你只要想用GPU 随时都可以用',maximum_dispatches=1,retries=0,formal_submission=False,maximum_seconds=18000,actual_four_L4_required=True,Agent_seconds=300)
files['GPU_AUTHORIZATION.json']=json.dumps(auth,indent=2,ensure_ascii=False).encode()
packed={n:base64.b64encode(b).decode() for n,b in files.items()}
old=(ROOT/'work/gemma-r12-01/authorized-gpu-02/study.ipynb').read_bytes()
code="""import base64,os,sys,json,hashlib,shutil,subprocess,time,traceback,textwrap,zipfile
from pathlib import Path
EGRD_STARTED=time.monotonic();RUN_DIR=Path('/kaggle/working/egrd-v01-12b-pilot01');RUN_DIR.mkdir(exist_ok=False)
RESULT=dict(status='STARTING',maximum_dispatches=1,retries=0,formal_submission=False)
"""
code+='OLD=json.loads(base64.b64decode('+repr(base64.b64encode(old).decode())+'))\nFILES='+repr(packed)+'\n'
code+='''try:
 import torch
 listing=subprocess.run(['nvidia-smi','-L'],capture_output=True,text=True,timeout=20)
 memory=subprocess.run(['nvidia-smi','--query-gpu=name,memory.total','--format=csv,noheader'],capture_output=True,text=True,timeout=20)
 allocation=dict(listing=listing.stdout,memory=memory.stdout,torch_count=torch.cuda.device_count(),devices=[dict(name=torch.cuda.get_device_name(i),memory=torch.cuda.get_device_properties(i).total_memory) for i in range(torch.cuda.device_count())])
 admitted=listing.returncode==0 and memory.returncode==0 and len(allocation['devices'])==4 and all(d['name']=='NVIDIA L4' and d['memory']>0 for d in allocation['devices'])
 if admitted:
  for i in range(4):
   tensor=torch.empty(1,device='cuda:'+str(i));torch.cuda.synchronize(i);del tensor
 allocation['status']='GPU_ALLOCATION_CONFIRMED' if admitted else 'GPU_ALLOCATION_FAILED'
 (RUN_DIR/'GPU_ALLOCATION.json').write_text(json.dumps(allocation,indent=2));assert admitted,'GPU_ALLOCATION_FAILED'
 first=OLD['cells'][0]['source'];second=OLD['cells'][1]['source']
 exec(compile(first[:first.index("guard['require_authorization']")],'accepted-bootstrap-definitions','exec'),globals())
 extension=RUN_DIR/'extension';extension.mkdir()
 for name,raw in BOOTSTRAP_FILES.items():(extension/name).write_bytes(raw)
 sys.path.insert(0,str(extension))
 exec(compile(first[first.index("SOURCE=RUN_DIR/'source'"):],'accepted-source-materialization','exec'),globals())
 install=textwrap.dedent(second[second.index(' import glob'):second.index(" assert allocation['status']")]);exec(compile(install,'accepted-pinned-offline-sdk-install','exec'),globals())
 SESSION_STARTED=EGRD_STARTED
 archives=list(Path('/kaggle/input').rglob('r2a-final-cpu-overlay.zip'));assert len(archives)==1
 assert hashlib.sha256(archives[0].read_bytes()).hexdigest()=='c8d306b82cb798a59e01dbade70ac2e9c5942a2fbf9105464b04c3ac1f78c875'
 parent=RUN_DIR/'parent';parent.mkdir()
 with zipfile.ZipFile(archives[0]) as z:
  assert z.testzip() is None and all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in z.namelist());z.extractall(parent)
  for info in z.infolist():
   if not info.is_dir():(parent/info.filename).chmod((info.external_attr>>16)&0o777 or 0o644)
 study=parent/'study';hardening=RUN_DIR/'hardening';hardening.mkdir()
 for n,b in FILES.items():
  p=hardening/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(base64.b64decode(b))
 (RUN_DIR/'RUN_INPUT_IDENTITIES.json').write_text(json.dumps({n:hashlib.sha256(base64.b64decode(b)).hexdigest() for n,b in FILES.items()},indent=2))
 os.environ['PYTHONPATH']=str(hardening)+os.pathsep+str(study)+os.pathsep+str(extension)+os.pathsep+str(SOURCE)
 from harness_v2.supervisor import supervise
 remaining=18000-(time.monotonic()-EGRD_STARTED)-900;assert remaining>=9300,'Insufficient complete12B pilot reserve'
 outcome=supervise([sys.executable,str(hardening/'pilot_coordinator.py'),str(RUN_DIR/'execution'),str(EGRD_STARTED)],RUN_DIR/'execution',outer_seconds=remaining,stage_caps=dict(load_model=1300,cleanup=180),cwd=SOURCE)
 (RUN_DIR/'NOTEBOOK_SUPERVISOR.json').write_text(json.dumps(outcome,indent=2));RESULT.update(status='EXECUTION_TERMINAL',supervisor=outcome)
except BaseException as exc:RESULT.update(status='ALLOCATION_OR_INFRASTRUCTURE_STOP',type=type(exc).__name__,reason=str(exc),traceback=traceback.format_exc())
finally:
 evidence=RUN_DIR/'evidence';evidence.mkdir()
 try:
  if 'extension' in globals():
   from r12_authorized_dispatch import recover_owned
   (evidence/'OWNED_ROOT_RECOVERY.json').write_text(json.dumps(recover_owned(RUN_DIR/'execution'),indent=2))
 except BaseException as exc:RESULT['recovery_error']=type(exc).__name__
 RESULT['elapsed_seconds']=time.monotonic()-EGRD_STARTED
 (evidence/'NOTEBOOK_FINAL_STATUS.json').write_text(json.dumps(RESULT,indent=2))
 for n in ['GPU_ALLOCATION.json','RUN_INPUT_IDENTITIES.json','NOTEBOOK_SUPERVISOR.json']:
  if (RUN_DIR/n).exists():shutil.copyfile(RUN_DIR/n,evidence/n)
 if (RUN_DIR/'execution').exists():shutil.move(str(RUN_DIR/'execution'),str(evidence/'execution'))
 if 'hardening' in globals():shutil.copytree(hardening,evidence/'dispatched-code')
 archive=shutil.make_archive('/kaggle/working/egrd-v01-12b-pilot01','zip',evidence)
 assert RUN_DIR.resolve()==Path('/kaggle/working/egrd-v01-12b-pilot01');shutil.rmtree(RUN_DIR)
 print('EGRD_PILOT_TERMINAL',json.dumps(RESULT),flush=True)
'''
compile(code,'egrd-gpu','exec');folder=D/'gpu-notebook';folder.mkdir(exist_ok=True)
nb=dict(nbformat=4,nbformat_minor=5,metadata=dict(kernelspec=dict(name='python3',language='python',display_name='Python 3')),cells=[dict(cell_type='code',id='egrd-gpu',metadata={},outputs=[],execution_count=None,source=code)])
(folder/'study.ipynb').write_text(json.dumps(nb,indent=1)+'\n')
meta=json.loads((D/'cpu-notebook/kernel-metadata.json').read_bytes());meta.update(id='wudangdexiaodoashi/egrd-v01-12b-pilot01',title='EGRD V01 12B Pilot01',enable_gpu=True,machine_shape='NvidiaL4',model_sources=[models['12b']['mount'],models['31b']['mount']]);(folder/'kernel-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
(folder/'GPU_AUTHORIZATION.json').write_bytes(files['GPU_AUTHORIZATION.json'])
(folder/'BUILD.json').write_text(json.dumps(dict(notebook_sha256=hashlib.sha256((folder/'study.ipynb').read_bytes()).hexdigest(),metadata_sha256=hashlib.sha256((folder/'kernel-metadata.json').read_bytes()).hexdigest(),authorization_sha256=hashlib.sha256(files['GPU_AUTHORIZATION.json']).hexdigest(),files={n:hashlib.sha256(b).hexdigest() for n,b in files.items()},CPU_archive_sha256=hashlib.sha256(cpu.read_bytes()).hexdigest(),maximum_seconds=18000,maximum_dispatches=1,required_quota_seconds=73200),indent=2)+'\n')
print('GPU_PILOT_BUILT_NOT_DISPATCHED')
