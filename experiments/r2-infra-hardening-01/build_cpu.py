"""New private CPU-only notebook over immutable previously admitted assets."""
import base64,hashlib,json
from pathlib import Path
D=Path(__file__).resolve().parent;old=D.parent/'r2-early-decision-01'
original=json.loads((old/'final-cpu-notebook/study.ipynb').read_bytes())['cells'][0]['source']
code=original[:original.index(" transports=list(")].replace('/kaggle/working/r2a-final-cpu-overlay','/kaggle/working/r2-infra-cpu-hardening-01')
modules=['stop_policy.py','hardened_runtime.py','hardened_worker.py','hardened_coordinator.py','cpu_integration.py']
packed={n:base64.b64encode((D/n).read_bytes()).decode() for n in modules}
code+=''' ready=list(Path('/kaggle/input').rglob('r2a-final-cpu-overlay.zip'));assert len(ready)==1
 assert hashlib.sha256(ready[0].read_bytes()).hexdigest()=='c8d306b82cb798a59e01dbade70ac2e9c5942a2fbf9105464b04c3ac1f78c875'
 import zipfile
 parent=RUN_DIR/'parent';parent.mkdir()
 with zipfile.ZipFile(ready[0]) as z:
  assert z.testzip() is None
  assert all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in z.namelist())
  z.extractall(parent)
  for info in z.infolist():
   if not info.is_dir():(parent/info.filename).chmod((info.external_attr>>16)&0o777 or 0o644)
 assert json.loads((parent/'CPU_FINAL_SUMMARY.json').read_bytes())['status']=='PASS'
 study=parent/'study'
 hardening=RUN_DIR/'hardening';hardening.mkdir()
'''
code+=' MODULES='+repr(packed)+'\n for n,b in MODULES.items():(hardening/n).write_bytes(base64.b64decode(b))\n'
code+=''' evidence=RUN_DIR/'evidence';evidence.mkdir()
 (evidence/'SOURCE_IDENTITIES.json').write_text(json.dumps({n:hashlib.sha256(base64.b64decode(b)).hexdigest() for n,b in MODULES.items()},indent=2))
 os.environ['PYTHONPATH']=str(hardening)+os.pathsep+str(study)+os.pathsep+str(extension)+os.pathsep+str(SOURCE)
 with (evidence/'integration.log').open('w') as log:
  result=subprocess.run([sys.executable,str(hardening/'cpu_integration.py'),str(evidence/'integration')],stdout=log,stderr=subprocess.STDOUT,timeout=2400)
 RESULT.update(status='PASS' if result.returncode==0 else 'CPU_INTEGRATION_BLOCKED',returncode=result.returncode)
 if (evidence/'integration/CPU_INTEGRATION_RESULTS.json').exists():RESULT['integration']=json.loads((evidence/'integration/CPU_INTEGRATION_RESULTS.json').read_bytes())
except BaseException as e:
 RESULT.update(status='CPU_INTEGRATION_BLOCKED',error_type=type(e).__name__,reason=str(e),traceback=traceback.format_exc())
finally:
 evidence=RUN_DIR/'evidence';evidence.mkdir(exist_ok=True)
 (evidence/'CPU_HARDENING_SUMMARY.json').write_text(json.dumps(RESULT,indent=2))
 print('CPU_HARDENING_TERMINAL',RESULT['status'],flush=True)
 # Only this job's evidence is exported; source/runtime inputs are disposable.
 archive=shutil.make_archive('/kaggle/working/r2-infra-cpu-hardening-01','zip',evidence)
 assert RUN_DIR.resolve()==Path('/kaggle/working/r2-infra-cpu-hardening-01')
 shutil.rmtree(RUN_DIR)
'''
compile(code,'new-cpu-hardening','exec')
folder=D/'cpu-notebook';folder.mkdir(exist_ok=True)
nb=dict(nbformat=4,nbformat_minor=5,metadata=dict(kernelspec=dict(name='python3',language='python',display_name='Python 3')),cells=[dict(cell_type='code',id='infra-cpu-only',metadata={},outputs=[],execution_count=None,source=code)])
(folder/'study.ipynb').write_text(json.dumps(nb,indent=1)+'\n')
meta=json.loads((old/'final-cpu-notebook/kernel-metadata.json').read_bytes())
meta.update(id='wudangdexiaodoashi/r2-infrastructure-cpu-hardening-01',title='R2 Infrastructure CPU Hardening 01',enable_gpu=False,enable_tpu=False,enable_internet=False,model_sources=[])
meta['kernel_sources'].append('wudangdexiaodoashi/r2a-final-cpu-overlay-01')
(folder/'kernel-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
(D/'BUILD.json').write_text(json.dumps(dict(CPU_only=True,model_sources=[],real_model_requests=0,modules={n:hashlib.sha256((D/n).read_bytes()).hexdigest() for n in modules},notebook_sha256=hashlib.sha256((folder/'study.ipynb').read_bytes()).hexdigest()),indent=2)+'\n')
print('CPU_NOTEBOOK_BUILT')
