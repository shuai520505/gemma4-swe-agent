"""CPU-only replay over admitted version-8 Linux assets; no model attached."""
import base64,hashlib,json,sys
from pathlib import Path
D=Path(__file__).resolve().parent;ROOT=D.parents[1]
old=(ROOT/'work/gemma-r12-01/authorized-gpu-02/study.ipynb').read_bytes()
names=('r2a_runtime.py','r2a_worker.py','r2a_coordinator.py','cpu_worker_replay.py','independent_exact_evaluator.py','APPROVED_EVALUATION_AMENDMENT.json')
overlays={n:base64.b64encode((D/n).read_bytes()).decode() for n in names}
code="""import base64,os,sys,json,hashlib,shutil,subprocess,time,traceback,textwrap
from pathlib import Path
RUN_DIR=Path('/kaggle/working/r2a-final-cpu-overlay');RUN_DIR.mkdir(exist_ok=False)
RESULT=dict(status='RUNNING',CPU_only=True,real_Gemma_requests=0,GPU_sessions=0)
"""
code+='OLD=json.loads(base64.b64decode('+repr(base64.b64encode(old).decode())+'))\nOVERLAYS='+repr(overlays)+'\nTRANSPORT_SHA='+repr(json.loads((D/'RUNTIME_TRANSPORT_IDENTITY.json').read_bytes())['sha256'])+'\n'
code+='''try:
 first=OLD['cells'][0]['source'];second=OLD['cells'][1]['source']
 exec(compile(first[:first.index("guard['require_authorization']")],'accepted-bootstrap-definitions','exec'),globals())
 extension=RUN_DIR/'extension';extension.mkdir()
 for name,raw in BOOTSTRAP_FILES.items():(extension/name).write_bytes(raw)
 sys.path.insert(0,str(extension))
 exec(compile(first[first.index("SOURCE=RUN_DIR/'source'"):],'accepted-source-materialization','exec'),globals())
 install=textwrap.dedent(second[second.index(' import glob'):second.index(" assert allocation['status']")])
 exec(compile(install,'accepted-pinned-offline-sdk-install','exec'),globals())
 import torch
 assert torch.cuda.device_count()==0
 transports=list(Path('/kaggle/input').rglob('R2A_LINUX_RUNTIME.bin'));assert len(transports)==1
 import zipfile
 assert hashlib.sha256(transports[0].read_bytes()).hexdigest()==TRANSPORT_SHA
 parent=RUN_DIR/'parent';parent.mkdir()
 with zipfile.ZipFile(transports[0]) as z:
  assert z.testzip() is None and all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in z.namelist())
  z.extractall(parent)
  for info in z.infolist():
   if not info.is_dir():(parent/info.filename).chmod((info.external_attr>>16)&0o777 or 0o644)
 summary=json.loads((parent/'CPU_ADMISSION_SUMMARY.json').read_bytes())
 assert summary['CPU_only'] and summary['model_requests']==0
 study=RUN_DIR/'study';shutil.copytree(parent/'study',study,symlinks=True)
 identities=json.loads((parent/'TASK_RUNTIME_311_IDENTITIES.json').read_bytes())
 for n,h in identities['files'].items():assert hashlib.sha256((study/n).read_bytes()).hexdigest()==h,n
 snaps=json.loads((parent/'SDK_SNAPSHOT_IDENTITIES.json').read_bytes())
 for row in snaps:
  archive=study/'assets/snapshots'/(row['task']+'.tgz')
  assert hashlib.sha256(archive.read_bytes()).hexdigest()==row['SDK_snapshot_sha256']
 for n,b in OVERLAYS.items():(study/n).write_bytes(base64.b64decode(b))
 (RUN_DIR/'RUNTIME_OVERLAY_IDENTITIES.json').write_text(json.dumps({n:hashlib.sha256(base64.b64decode(b)).hexdigest() for n,b in OVERLAYS.items()},indent=2))
 for n in ('TASK_RUNTIME_311_IDENTITIES.json','SDK_SNAPSHOT_IDENTITIES.json','SOURCE_TREE_VERIFICATION.json'):
  shutil.copyfile(parent/n,RUN_DIR/n)
 os.environ['PYTHONPATH']=str(study)+os.pathsep+str(extension)+os.pathsep+str(SOURCE)
 subprocess.run([sys.executable,str(study/'independent_exact_evaluator.py')],check=True,timeout=30)
 with (RUN_DIR/'admission-worker.log').open('w') as log:
  admit=subprocess.run([sys.executable,str(study/'r2a_runtime.py'),str(RUN_DIR/'admission')],stdout=log,stderr=subprocess.STDOUT,timeout=6000)
 RESULT['admission']=json.loads((RUN_DIR/'admission/ADMISSION_RESULTS.json').read_bytes())
 assert admit.returncode==0 and RESULT['admission']['status']=='PASS','CPU_ADMISSION_NOT_PASS'
 with (RUN_DIR/'replay-worker.log').open('w') as log:
  replay=subprocess.run([sys.executable,str(study/'cpu_worker_replay.py'),str(RUN_DIR/'replay')],stdout=log,stderr=subprocess.STDOUT,timeout=1800)
 contract=RUN_DIR/'replay/CPU_REPLAY_CONTRACT.json'
 RESULT['plumbing_replay']=json.loads(contract.read_bytes()) if contract.exists() else None
 RESULT['replay_returncode']=replay.returncode
 RESULT['status']='PASS' if replay.returncode==0 and RESULT['plumbing_replay'] and RESULT['plumbing_replay']['status']=='PASS_PLUMBING_ONLY' else 'CPU_REPLAY_BLOCKED'
except BaseException as e:RESULT.update(status='CPU_INTEGRATION_BLOCKED',error_type=type(e).__name__,reason=str(e),traceback=traceback.format_exc())
finally:
 (RUN_DIR/'CPU_FINAL_SUMMARY.json').write_text(json.dumps(RESULT,indent=2))
 print('R2A_CPU_FINAL',json.dumps(RESULT),flush=True)
 # Remove duplicated transport extraction before saving the ready local study.
 if 'parent' in globals() and parent.parent==RUN_DIR:shutil.rmtree(parent)
 archive=shutil.make_archive(str(RUN_DIR),'zip',RUN_DIR)
 print('EVIDENCE_ARCHIVE',archive,flush=True)
 assert RUN_DIR.parent==Path('/kaggle/working') and RUN_DIR.name=='r2a-final-cpu-overlay'
 shutil.rmtree(RUN_DIR)
'''
diagnostic='--diagnostic' in sys.argv
if diagnostic:
 start=code.index(" with (RUN_DIR/'admission-worker.log').open('w') as log:")
 end=code.index('except BaseException as e:RESULT.update',start)
 diagnostic_child="from pathlib import Path\nfrom r2a_runtime import SubprocessManager,Journal,HERE\nout=Path('/kaggle/working/r2a-final-cpu-overlay/diagnostic');out.mkdir()\nm=SubprocessManager(journal=Journal(out),base_dir=out/'roots',task_wheels=HERE/'assets/wheels',timeout_seconds=240,project_version='2022.03')\ntry:m.start()\nfinally:m.cleanup_all()\n"
 code=code[:start]+" with (RUN_DIR/'diagnostic-worker.log').open('w') as log:\n  p=subprocess.run([sys.executable,'-c',"+repr(diagnostic_child)+"],stdout=log,stderr=subprocess.STDOUT,timeout=900)\n RESULT.update(status='DIAGNOSTIC_COMPLETE_NOT_ADMISSION',diagnostic_returncode=p.returncode)\n"+code[end:]
compile(code,'overlay-cpu','exec')
folder=D/('diagnostic-cpu-notebook' if diagnostic else 'final-cpu-notebook');folder.mkdir(exist_ok=True)
nb=dict(nbformat=4,nbformat_minor=5,metadata=dict(kernelspec=dict(name='python3',language='python',display_name='Python 3')),cells=[dict(cell_type='code',execution_count=None,id='r2afinalcpu',metadata={},outputs=[],source=code)])
(folder/'study.ipynb').write_text(json.dumps(nb,indent=1)+'\n')
meta=json.loads((D/'cpu-notebook/kernel-metadata.json').read_bytes())
meta.update(id='wudangdexiaodoashi/r2a-runtime-cpu-diagnostic-01' if diagnostic else 'wudangdexiaodoashi/r2a-final-cpu-overlay-01',title='R2A Runtime CPU Diagnostic 01' if diagnostic else 'R2A Final CPU Overlay 01',enable_internet=False)
meta['dataset_sources'].append('wudangdexiaodoashi/r2a-linux-runtime-inputs-20261101')
(folder/'kernel-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
print('Built offline CPU overlay:',folder)
