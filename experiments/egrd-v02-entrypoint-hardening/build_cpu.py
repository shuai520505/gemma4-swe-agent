"""Prepare a CPU-only Notebook; this builder never calls SaveKernel."""
import base64,hashlib,json,argparse
from pathlib import Path
D=Path(__file__).resolve().parent;ROOT=D.parents[1];OLD=D.parent/'r2-infra-hardening-01'
p=argparse.ArgumentParser();p.add_argument('--prepare-recheck',action='store_true');args=p.parse_args()
assert args.prepare_recheck,'Original dispatched CPU build is immutable; only prepare a new, unauthorized recheck'
slug='egrd-v02-cpu-hardening03'
source=json.loads((OLD/'cpu-notebook/study.ipynb').read_bytes())['cells'][0]['source']
code=source[:source.index(' MODULES=')].replace('r2-infra-cpu-hardening-01',slug)
names=['core.py','meer_verifier.py','skill_cli.py','sdk_acceptance.py','sdk_context_check.py','cpu_sdk.py','worker_cpu.py','runtime_adapter.py','hardened_runtime.py','source_binding.py','inherited_hardened_runtime.py','stop_policy.py','pilot_worker.py','pilot_coordinator.py','timing.py','activation.py','result_contract.py','supervision.py','worker_contract_fixture.py','model_selection.py','RUNTIME_LOCK.json','MODEL_CONFIGURATIONS.json','PACKAGE_MANIFEST.json','SMOKE_TASK_LOCK.json','ISSUES.agent.json']
files={n:(D/n).read_bytes() for n in names}
files.update({p.name:p.read_bytes() for p in D.glob('test_*.py')})
for folder in ['packages','legacy_tests']:
 files.update({p.relative_to(D).as_posix():p.read_bytes() for p in (D/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts})
files['infra_legacy_tests/test_stop_policy.py']=(OLD/'test_stop_policy.py').read_bytes()
files['r2-early-decision-01/r2a_coordinator.py']=(D.parent/'r2-early-decision-01/r2a_coordinator.py').read_bytes()
files['r2-early-decision-01/results/06_A_sphinx-doc__sphinx-11445/TOOL_ACTIONS.json']=(D.parent/'r2-early-decision-01/results/06_A_sphinx-doc__sphinx-11445/TOOL_ACTIONS.json').read_bytes()
code+=' MODULES='+repr({n:base64.b64encode(b).decode() for n,b in files.items()})+'\n'
code+=""" for n,b in MODULES.items():
  p=hardening/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(base64.b64decode(b))
 evidence=RUN_DIR/'evidence';evidence.mkdir()
 (evidence/'SOURCE_IDENTITIES.json').write_text(json.dumps({n:hashlib.sha256(base64.b64decode(b)).hexdigest() for n,b in MODULES.items()},indent=2))
 os.environ['PYTHONPATH']=str(hardening)+os.pathsep+str(study)+os.pathsep+str(extension)+os.pathsep+str(SOURCE)
 os.environ['PYTHONDONTWRITEBYTECODE']='1'
 stages=[]
 commands=[('legacy27',[sys.executable,'-m','unittest','discover','-s',str(hardening/'legacy_tests'),'-p','test_*.py']),('infra6',[sys.executable,str(hardening/'infra_legacy_tests/test_stop_policy.py')]),('new_tests',[sys.executable,'-m','unittest','discover','-s',str(hardening),'-p','test_*.py']),('compiler',[sys.executable,str(hardening/'sdk_acceptance.py')]),('SDK_context_clock',[sys.executable,str(hardening/'sdk_context_check.py')]),('skill',[sys.executable,str(hardening/'cpu_sdk.py'),str(evidence/'sdk')]),('worker',[sys.executable,str(hardening/'worker_cpu.py'),str(evidence/'worker')])]
 for label,command in commands:
  (hardening/'evidence').mkdir(exist_ok=True)
  with (evidence/(label+'.log')).open('w') as log:r=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=1200)
  stages.append(dict(stage=label,returncode=r.returncode))
  if r.returncode:break
 RESULT.update(status='PASS' if len(stages)==7 and all(s['returncode']==0 for s in stages) else 'BLOCKED_INFRASTRUCTURE',stages=stages,GPU=0,real_Gemma_requests=0)
 for name in ['SDK_COMPILER.json','SDK_TOOL_SCHEMAS.json','SDK_CONTEXT_CLOCK_CHECK.json']:
  if (hardening/'evidence'/name).exists():shutil.copyfile(hardening/'evidence'/name,evidence/name)
except BaseException as exc:RESULT.update(status='BLOCKED_INFRASTRUCTURE',type=type(exc).__name__,reason=str(exc),traceback=traceback.format_exc())
finally:
 evidence=RUN_DIR/'evidence';evidence.mkdir(exist_ok=True)
 (evidence/'CPU_SUMMARY.json').write_text(json.dumps(RESULT,indent=2));print('EGRD_V02_CPU_TERMINAL',RESULT['status'],flush=True)
 archive=shutil.make_archive('/kaggle/working/egrd-v02-cpu-hardening01','zip',evidence)
 assert RUN_DIR.resolve()==Path('/kaggle/working/egrd-v02-cpu-hardening01');shutil.rmtree(RUN_DIR)
"""
code=code.replace('egrd-v02-cpu-hardening01',slug)
compile(code,'cpu-v02','exec');folder=D/'cpu03-prepared';folder.mkdir(exist_ok=True)
assert not (folder/'dispatch').exists(),'Never overwrite a dispatched CPU Notebook'
nb=dict(nbformat=4,nbformat_minor=5,metadata=dict(kernelspec=dict(name='python3',language='python',display_name='Python 3')),cells=[dict(cell_type='code',id='v02-cpu',metadata={},outputs=[],execution_count=None,source=code)])
(folder/'study.ipynb').write_text(json.dumps(nb,indent=1)+'\n')
meta=json.loads((OLD/'cpu-notebook/kernel-metadata.json').read_bytes());meta.update(id='wudangdexiaodoashi/'+slug,title='EGRD V02 CPU Hardening03',enable_gpu=False,enable_tpu=False,model_sources=[])
(folder/'kernel-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
(folder/'BUILD.json').write_text(json.dumps(dict(notebook_sha256=hashlib.sha256((folder/'study.ipynb').read_bytes()).hexdigest(),metadata_sha256=hashlib.sha256((folder/'kernel-metadata.json').read_bytes()).hexdigest(),files={n:hashlib.sha256(b).hexdigest() for n,b in files.items()},GPU=False,real_Gemma_requests=0,SaveKernel_authorized=False,status='PREPARED_NOT_DISPATCHED'),indent=2))
print('CPU_ONLY_PREPARED_NO_SAVEKERNEL')
