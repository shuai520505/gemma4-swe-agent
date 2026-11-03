import base64,hashlib,json
from pathlib import Path
D=Path(__file__).resolve().parent
old=D.parent/'r2-infra-hardening-01'
source=json.loads((old/'cpu-notebook/study.ipynb').read_bytes())['cells'][0]['source']
code=source[:source.index(' MODULES=')].replace('r2-infra-cpu-hardening-01','egrd-v01-12b-cpu01')
files={n:(D/n).read_bytes() for n in ['core.py','meer_verifier.py','skill_cli.py','test_core.py','test_state_edges.py','test_packages.py','MODEL_CONFIGURATIONS.json','TASK_IDENTITY_MANIFEST.json','sdk_acceptance.py','cpu_sdk.py','PACKAGE_MANIFEST.json','runtime_adapter.py','pilot_worker.py','worker_cpu.py']}
for n in ['hardened_runtime.py','stop_policy.py']:files[n]=(old/n).read_bytes()
files.update({p.relative_to(D).as_posix():p.read_bytes() for p in (D/'packages').rglob('*') if p.is_file()})
packed={n:base64.b64encode(b).decode() for n,b in files.items()}
code+=' MODULES='+repr(packed)+'\n'
code+=''' for n,b in MODULES.items():
  p=hardening/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(base64.b64decode(b))
 evidence=RUN_DIR/'evidence';evidence.mkdir()
 (evidence/'SOURCE_IDENTITIES.json').write_text(json.dumps({n:hashlib.sha256(base64.b64decode(b)).hexdigest() for n,b in MODULES.items()},indent=2))
 model=Path('/kaggle/input/models/google/gemma-4/other/gemma-4-12b-it-qat-w4a16-ct/2')
 assert model.is_dir() and (model/'model.safetensors').is_file()
 hashes={}
 for p in model.rglob('*'):
  if p.is_file():
   with p.open('rb') as f:hashes[p.relative_to(model).as_posix()]=hashlib.file_digest(f,'sha256').hexdigest()
 (evidence/'MODEL_12B_MOUNT.json').write_text(json.dumps(dict(source='google/gemma-4/Other/gemma-4-12b-it-qat-w4a16-ct/2',files=hashes,weights_loaded=False,model_requests=0),indent=2))
 os.environ['PYTHONPATH']=str(hardening)+os.pathsep+str(study)+os.pathsep+str(extension)+os.pathsep+str(SOURCE)
 stages=[]
 for label,command in [('units',[sys.executable,'-m','unittest','discover','-s',str(hardening),'-p','test_*.py']),('compiler',[sys.executable,str(hardening/'sdk_acceptance.py')]),('skill',[sys.executable,str(hardening/'cpu_sdk.py'),str(evidence/'sdk')]),('worker',[sys.executable,str(hardening/'worker_cpu.py'),str(evidence/'worker')])]:
  (hardening/'evidence').mkdir(exist_ok=True)
  with (evidence/(label+'.log')).open('w') as log:r=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=1200)
  stages.append(dict(stage=label,returncode=r.returncode))
  if r.returncode:break
 RESULT.update(status='PASS' if len(stages)==4 and all(s['returncode']==0 for s in stages) else 'CPU_INTEGRATION_BLOCKED',stages=stages)
 if (hardening/'evidence/SDK_COMPILER.json').exists():shutil.copyfile(hardening/'evidence/SDK_COMPILER.json',evidence/'SDK_COMPILER.json')
except BaseException as e:RESULT.update(status='CPU_INTEGRATION_BLOCKED',type=type(e).__name__,reason=str(e),traceback=traceback.format_exc())
finally:
 evidence=RUN_DIR/'evidence';evidence.mkdir(exist_ok=True)
 (evidence/'CPU_SUMMARY.json').write_text(json.dumps(RESULT,indent=2))
 print('EGRD_CPU_TERMINAL',RESULT['status'],flush=True)
 archive=shutil.make_archive('/kaggle/working/egrd-v01-12b-cpu01','zip',evidence)
 assert RUN_DIR.resolve()==Path('/kaggle/working/egrd-v01-12b-cpu01')
 shutil.rmtree(RUN_DIR)
'''
compile(code,'egrd-cpu','exec');folder=D/'cpu-notebook';folder.mkdir(exist_ok=True)
nb=dict(nbformat=4,nbformat_minor=5,metadata=dict(kernelspec=dict(name='python3',language='python',display_name='Python 3')),cells=[dict(cell_type='code',id='egrd-cpu',metadata={},outputs=[],execution_count=None,source=code)])
(folder/'study.ipynb').write_text(json.dumps(nb,indent=1)+'\n')
meta=json.loads((old/'cpu-notebook/kernel-metadata.json').read_bytes());meta.update(id='wudangdexiaodoashi/egrd-v01-12b-cpu01',title='EGRD V01 12B CPU01',enable_gpu=False,enable_tpu=False,model_sources=['google/gemma-4/Other/gemma-4-12b-it-qat-w4a16-ct/2'])
(folder/'kernel-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
(D/'CPU_BUILD.json').write_text(json.dumps(dict(notebook_sha256=hashlib.sha256((folder/'study.ipynb').read_bytes()).hexdigest(),files={n:hashlib.sha256(b).hexdigest() for n,b in files.items()},GPU=False),indent=2)+'\n')
print('CPU_BUILT')
