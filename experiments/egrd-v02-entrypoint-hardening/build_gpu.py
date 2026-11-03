"""Prepare separate primary/fallback notebooks. No SaveKernel or authorization creation."""
import base64,hashlib,json,argparse
from pathlib import Path
D=Path(__file__).resolve().parent;ROOT=D.parents[1]
p=argparse.ArgumentParser();p.add_argument('--authorization-file');args=p.parse_args()
authorization=json.loads(Path(args.authorization_file).read_bytes()) if args.authorization_file else None
sha=lambda b:hashlib.sha256(b).hexdigest()
for name,expected in json.loads((D/'BOOTSTRAP_IDENTITIES.json').read_bytes()).items():
 assert sha((ROOT/name).read_bytes())==expected,'Inherited bootstrap identity changed'
names=['runtime_adapter.py','pilot_worker.py','pilot_coordinator.py','PACKAGE_MANIFEST.json','SMOKE_TASK_LOCK.json','ISSUES.agent.json','MODEL_CONFIGURATIONS.json','RUNTIME_LOCK.json','hardened_runtime.py','source_binding.py','inherited_hardened_runtime.py','stop_policy.py','timing.py','activation.py','supervision.py','result_contract.py','model_selection.py']
files={n:(D/n).read_bytes() for n in names}
files.update({p.relative_to(D).as_posix():p.read_bytes() for p in (D/'packages').rglob('*') if p.is_file() and '__pycache__' not in p.parts})
proof=D/'cpu02-evidence/CPU_SUMMARY.json'
cpu=json.loads(proof.read_bytes()) if proof.exists() else {'status':'NOT_RUN'}
cpu_ok=cpu.get('status')=='PASS' and len(cpu.get('stages',[]))==7
if cpu_ok:
 from result_contract import native_execution_check
 native_integrity=native_execution_check(D/'cpu02-evidence/worker/trusted/NATIVE_RESULT.json')
 cpu_ok=native_integrity['passed']
if cpu_ok:
 accepted=json.loads((D/'cpu02-evidence/SOURCE_IDENTITIES.json').read_bytes())
 assert all(n in accepted and sha(b)==accepted[n] for n,b in files.items()),'Runtime or package differs from actual CPU acceptance'
 assert json.loads((D/'cpu02-evidence/worker/WORKER_CPU_ACCEPTANCE.json').read_bytes())['status']=='PASS_PLUMBING_ONLY'
files['CPU_PROOF.json']=json.dumps(dict(summary=cpu,passed=cpu_ok,archive=json.loads((D/'cpu02-output/ARCHIVE.json').read_bytes()) if cpu_ok else None),indent=2).encode()
ids={n:sha(b) for n,b in files.items()}
old=(ROOT/'work/gemma-r12-01/authorized-gpu-02/study.ipynb').read_bytes()
template=(D.parent/'egrd-v01-12b/build_gpu.py').read_text(encoding='utf8')
# Reuse only the accepted bootstrap code string; do not execute the old builder.
import ast
tree=ast.parse(template)
suffix=next(n.value for n in tree.body if isinstance(n,ast.AugAssign) and isinstance(n.target,ast.Name) and n.target.id=='code' and isinstance(n.value,ast.Constant))
bootstrap=suffix.value
bootstrap=bootstrap[:bootstrap.index(' from harness_v2.supervisor import supervise')]
bootstrap=bootstrap.replace(' for n,b in FILES.items():',' for n,b in FILES.items():')
for model in ['12b','31b']:
 slug='egrd-v02-'+model+'-smoke01';folder=D/('gpu-'+model+'-prepared');folder.mkdir(exist_ok=True)
 code="import base64,os,sys,json,hashlib,shutil,subprocess,time,traceback,textwrap,zipfile\nfrom pathlib import Path\n"
 code+="EGRD_STARTED=time.monotonic();RUN_DIR=Path('/kaggle/working/"+slug+"');RUN_DIR.mkdir(exist_ok=False)\nRESULT=dict(status='STARTING',formal_submission=False,retries=0)\n"
 code+='OLD=json.loads(base64.b64decode('+repr(base64.b64encode(old).decode())+'))\nFILES='+repr({n:base64.b64encode(b).decode() for n,b in files.items()})+'\n'
 selected_auth=authorization if authorization and authorization.get('model')==model else None
 if selected_auth:
  assert cpu_ok and selected_auth['user_answer']=='允许CPU和GPU' and selected_auth['explicit_GPU_confirmation'] is True
  assert selected_auth['maximum_dispatches']==1 and selected_auth['retries']==0
 code+='AUTHORIZATION='+repr(selected_auth)+'\nCPU_PASSED='+repr(cpu_ok)+'\n'
 code+="""try:
 assert CPU_PASSED,'CPU_ACCEPTANCE_REQUIRED'
 assert isinstance(AUTHORIZATION,dict) and AUTHORIZATION.get('explicit_GPU_confirmation') is True,'NEW_HUMAN_GPU_CONFIRMATION_REQUIRED'
 assert AUTHORIZATION.get('model')=="""+repr(model)+"\n"
 code+=" assert AUTHORIZATION.get('maximum_dispatches')==1 and AUTHORIZATION.get('retries')==0\n"
 # Existing prefix begins try; use its inner body under our new authorization gate.
 body=bootstrap[bootstrap.index(' import torch'):]
 code+=body
 code+=""" from supervision import supervise
 remaining=18000-(time.monotonic()-EGRD_STARTED)-900
 assert remaining>=4500,'INSUFFICIENT_SMOKE_AND_ARCHIVE_RESERVE'
 confirmation_sha=hashlib.sha256(json.dumps(AUTHORIZATION,sort_keys=True).encode()).hexdigest()
 outcome=supervise([sys.executable,str(hardening/'pilot_coordinator.py'),str(RUN_DIR/'execution'),str(EGRD_STARTED),"""+repr(model)+""",confirmation_sha],RUN_DIR/'execution',role='aggregate',outer_seconds=remaining,stage_caps=dict(load_model=1300,cleanup=180),cwd=SOURCE)
 (RUN_DIR/'NOTEBOOK_SUPERVISOR.json').write_text(json.dumps(outcome,indent=2))
 RESULT.update(status='EXECUTION_TERMINAL',supervisor=outcome)
except BaseException as exc:
 RESULT.update(status='PRECONDITION_OR_INFRASTRUCTURE_STOP',type=type(exc).__name__,reason=str(exc),traceback=traceback.format_exc())
finally:
 evidence=RUN_DIR/'evidence';evidence.mkdir(exist_ok=True)
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
"""
 code+=" archive=shutil.make_archive('/kaggle/working/"+slug+"','zip',evidence)\n assert RUN_DIR.resolve()==Path('/kaggle/working/"+slug+"');shutil.rmtree(RUN_DIR)\n print('EGRD_V02_TERMINAL',json.dumps(RESULT),flush=True)\n"
 compile(code,slug,'exec')
 nb=dict(nbformat=4,nbformat_minor=5,metadata=dict(kernelspec=dict(name='python3',language='python',display_name='Python 3')),cells=[dict(cell_type='code',id=slug,metadata={},outputs=[],execution_count=None,source=code)])
 (folder/'study.ipynb').write_text(json.dumps(nb,indent=1)+'\n')
 models=json.loads((D/'MODEL_CONFIGURATIONS.json').read_bytes())
 meta=json.loads((D/'cpu-notebook/kernel-metadata.json').read_bytes())
 meta.update(id='wudangdexiaodoashi/'+slug,title='EGRD V02 '+model+' Smoke01',enable_gpu=True,machine_shape='NvidiaL4',model_sources=[models[model]['mount']])
 (folder/'kernel-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
 if selected_auth:(folder/'GPU_AUTHORIZATION.json').write_text(json.dumps(selected_auth,ensure_ascii=False,indent=2),encoding='utf8')
 (folder/'DISPATCH_CONFIG.json').write_text(json.dumps(dict(status='AUTHORIZED_CPU_PASSED_NOT_DISPATCHED' if selected_auth else 'PREPARED_NOT_DISPATCHED',model=model,CPU_passed=cpu_ok,human_GPU_confirmation_required=not bool(selected_auth),authorization_embedded=bool(selected_auth),requires_rebuild_after_confirmation=not bool(selected_auth),maximum_dispatches=1,retries=0,maximum_seconds=18000,required_quota_seconds=73200,required_devices='4 x NVIDIA L4 observed',claim_path=slug+'/dispatch/ONE_SHOT_CLAIM.json',fallback_automatic=False,formal_submission=False,notebook_sha256=sha((folder/'study.ipynb').read_bytes()),metadata_sha256=sha((folder/'kernel-metadata.json').read_bytes()),files=ids),indent=2)+'\n')
print('TWO_SEPARATE_NOTEBOOKS_PREPARED_NO_SAVEKERNEL')
