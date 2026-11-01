"""Build a compact CPU Notebook reusing the accepted mounted bootstrap."""
import base64,hashlib,json,shutil,zipfile
from pathlib import Path
D=Path(__file__).resolve().parent;ROOT=D.parents[1]
sha=lambda b:hashlib.sha256(b).hexdigest()
upload=D/'input-upload';upload.mkdir(exist_ok=True)
bundle=upload/'R2A_INPUTS.zip'
names=['PROTOCOL_AMENDMENT.json','TASK_IDENTITY_LOCK.json','ISSUES.agent.json','TRUSTED_TEST_SPEC.private.json','EXECUTION_PLAN.json','ASSET_MANIFEST.json','SOURCE_ACQUISITION.json','r2a_runtime.py']
with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED) as z:
    for n in names:z.write(D/n,n)
    for sub in ('assets','candidates'):
        for p in (D/sub).rglob('*'):
            if p.is_file():z.write(p,p.relative_to(D).as_posix())
manifest=dict(bundle_sha256=sha(bundle.read_bytes()),reference_patch_included=False,trusted_test_spec_isolated_from_Agent=True,model_assets_included=False)
(upload/'R2A_BUNDLE_IDENTITY.json').write_text(json.dumps(manifest,indent=2)+'\n')
metadata=dict(id='wudangdexiaodoashi/r2a-independent-inputs-20261101',title='R2A Independent Inputs 20261101',licenses=[dict(name='other')],description='Private experiment: four frozen public SWE-bench original Issues, upstream base snapshots with licenses, pinned runtime distributions, and evaluator-only test specifications. No reference repair or model weights. Same shared environment for both arms.')
(upload/'dataset-metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
old=(ROOT/'work/gemma-r12-01/authorized-gpu-02/study.ipynb').read_bytes()
code='''import os,sys,json,hashlib,zipfile,subprocess,shutil,time,traceback,base64,textwrap
from pathlib import Path
RUN_DIR=Path('/kaggle/working/r2a-cpu-admission-01');RUN_DIR.mkdir(exist_ok=False)
RESULT=dict(status='RUNNING',CPU_only=True,model_requests=0,GPU_sessions=0)
'''
code+=f"OLD=json.loads(base64.b64decode({base64.b64encode(old).decode()!r}))\nBUNDLE_SHA={manifest['bundle_sha256']!r}\n"
remote=D/'remote-identity/R2A_BUNDLE_IDENTITY.json'
if remote.exists():
    pinned=json.loads(remote.read_bytes())['bundle_sha256']
    code=code.replace('BUNDLE_SHA='+repr(manifest['bundle_sha256']),'BUNDLE_SHA='+repr(pinned))
overlays={n:base64.b64encode((D/n).read_bytes()).decode() for n in ('r2a_runtime.py','r2a_worker.py','r2a_coordinator.py','cpu_worker_replay.py','verify_source_trees.py','OFFICIAL_COMMIT_IDENTITIES.json','XARRAY_ARCHIVAL_ORIGINAL.json')}
for name in ('R2','A'):overlays['candidates/'+name+'.zip']=base64.b64encode((D/'candidates'/(name+'.zip')).read_bytes()).decode()
code+='OVERLAYS='+repr(overlays)+'\n'
expected_root={n:sha((D/n).read_bytes()) for n in names if n!='r2a_runtime.py'}
code+='EXPECTED_ROOT='+repr(expected_root)+'\n'
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
 study=RUN_DIR/'study';study.mkdir()
 bundles=list(Path('/kaggle/input').rglob('R2A_INPUTS.zip'))
 if bundles:
  assert len(bundles)==1
  raw=bundles[0].read_bytes();assert hashlib.sha256(raw).hexdigest()==BUNDLE_SHA
  with zipfile.ZipFile(__import__('io').BytesIO(raw)) as z:
   assert z.testzip() is None and all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in z.namelist())
   z.extractall(study)
 else:
  expanded=[p for p in Path('/kaggle/input').rglob('EXECUTION_PLAN.json') if p.parent.name=='R2A_INPUTS']
  assert len(expanded)==1
  shutil.copytree(expanded[0].parent,study,dirs_exist_ok=True)
  RESULT['mount_layout']='KAGGLE_EXPANDED_ARCHIVE'
 for n,h in EXPECTED_ROOT.items():assert hashlib.sha256((study/n).read_bytes()).hexdigest()==h,n
 asset=json.loads((study/'ASSET_MANIFEST.json').read_bytes())
 for n,h in asset['files'].items():assert hashlib.sha256((study/'assets'/n).read_bytes()).hexdigest()==h,n
 # Exact shared runtime overlay is frozen into Notebook source; no SDK/tool or candidate edits.
 for n,b in OVERLAYS.items():(study/n).write_bytes(base64.b64decode(b))
 (RUN_DIR/'RUNTIME_OVERLAY_IDENTITIES.json').write_text(json.dumps({n:hashlib.sha256(base64.b64decode(b)).hexdigest() for n,b in OVERLAYS.items()},indent=2))
 # Undo only GitHub export-subst metadata; assert all four complete Git trees afterward.
 import tarfile,io,copy
 archival=json.loads((study/'XARRAY_ARCHIVAL_ORIGINAL.json').read_bytes())
 target=study/'assets/snapshots/pydata__xarray-6599.tgz';temp=target.with_suffix('.normalized.tgz')
 restored=archival['original_text'].encode()
 assert hashlib.sha1(b'blob '+str(len(restored)).encode()+b'\\0'+restored).hexdigest()==archival['git_blob_sha']
 with tarfile.open(target,'r:gz') as src,tarfile.open(temp,'w:gz') as dst:
  for info in src.getmembers():
   f=src.extractfile(info) if info.isfile() else None
   if info.name.endswith('/.git_archival.txt'):
    info=copy.copy(info);info.size=len(restored);f=io.BytesIO(restored)
   dst.addfile(info,f)
 temp.replace(target)
 subprocess.run([sys.executable,str(study/'verify_source_trees.py')],check=True,timeout=60)
 identities=json.loads((study/'SOURCE_TREE_VERIFICATION.json').read_bytes())
 assert all(r['exact_git_tree_match'] for r in identities)
 (RUN_DIR/'SOURCE_TREE_VERIFICATION.json').write_text(json.dumps(identities,indent=2))
 # Native SDK snapshots are rooted at workspace contents, not a codeload wrapper directory.
 flat=[]
 for ident in identities:
  archive=study/'assets/snapshots'/(ident['task']+'.tgz');tmp=archive.with_suffix('.sdk.tgz')
  with tarfile.open(archive,'r:gz') as src,tarfile.open(tmp,'w:gz') as dst:
   for m in src.getmembers():
    parts=Path(m.name).parts[1:]
    if not parts:continue
    item=copy.copy(m);item.name=Path(*parts).as_posix();item.pax_headers={k:v for k,v in m.pax_headers.items() if k not in ('path','linkpath')}
    dst.addfile(item,src.extractfile(m) if m.isfile() else None)
  tmp.replace(archive)
  flat.append(dict(task=ident['task'],canonical_git_tree=ident['git_tree'],SDK_snapshot_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),wrapper_directory_removed=True,source_file_bytes_unchanged=True))
 (RUN_DIR/'SDK_SNAPSHOT_IDENTITIES.json').write_text(json.dumps(flat,indent=2))
 # Compatibility-only interpreter/dependency surface, identical for both arms.
 # Model server, official SDK and its tools continue to run under pinned host Python 3.12.
 tools=RUN_DIR/'uvtool'
 subprocess.run([sys.executable,'-m','pip','--isolated','install','--index-url','https://pypi.org/simple','--no-deps','--target',str(tools),'uv==0.8.22'],check=True,timeout=180)
 env=dict(os.environ,PYTHONPATH=str(tools),UV_NATIVE_TLS='true')
 subprocess.run([sys.executable,'-m','uv','python','install','3.11.9','--install-dir',str(RUN_DIR/'managed-python')],env=env,check=True,timeout=600)
 python=next((RUN_DIR/'managed-python').rglob('bin/python3.11'))
 assert subprocess.check_output([str(python),'--version'],text=True).strip()=='Python 3.11.9'
 shutil.copytree(python.parent.parent,study/'runtime311',symlinks=True)
 wheels=study/'assets/wheels';shutil.rmtree(wheels);wheels.mkdir()
 old_asciitree=list(Path('/kaggle/input').rglob('asciitree-0.3.3-py3-none-any.whl'));assert old_asciitree
 shutil.copyfile(old_asciitree[0],wheels/old_asciitree[0].name)
 required=['numpy==1.23.5','pandas==1.5.3','scipy==1.10.1','hypothesis==6.131.9','mpmath==1.3.0','pytest==8.4.2','pytest-xdist==3.6.1','pytest-timeout==2.3.1','setuptools==75.8.0','setuptools-scm==8.1.0','wheel==0.45.1','packaging==26.1','pip==24.1.2','pylint==3.0.0','Sphinx==7.2.6','dask==2022.9.2','zarr==2.16.1','numcodecs==0.11.0','asciitree==0.3.3']
 with (RUN_DIR/'task311-wheel-download.log').open('w') as log:
  subprocess.run([sys.executable,'-m','pip','--isolated','download','--index-url','https://pypi.org/simple','--find-links',str(wheels),'--only-binary=:all:','--platform','manylinux2014_x86_64','--python-version','311','--implementation','cp','--abi','cp311','-d',str(wheels)]+required,stdout=log,stderr=subprocess.STDOUT,timeout=900,check=True)
 for p in list(wheels.glob('*.whl')):
  if p.name.split('-')[0].lower() in {'pylint','sphinx','sympy','xarray'}:p.unlink()
 runtime_files={p.relative_to(study).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for sub in ('runtime311','assets/wheels') for p in (study/sub).rglob('*') if p.is_file() and p.suffix!='.pyc' and not p.is_symlink()}
 (RUN_DIR/'TASK_RUNTIME_311_IDENTITIES.json').write_text(json.dumps(dict(Python='3.11.9',files=runtime_files,source_versions=required,host_SDK_unchanged=True),indent=2))
 os.environ['PYTHONPATH']=str(study)+os.pathsep+str(extension)+os.pathsep+str(SOURCE)
 with (RUN_DIR/'admission-worker.log').open('w') as log:
  p=subprocess.run([sys.executable,str(study/'r2a_runtime.py'),str(RUN_DIR/'admission')],stdout=log,stderr=subprocess.STDOUT,timeout=7200)
 RESULT['worker_returncode']=p.returncode
 result=RUN_DIR/'admission/ADMISSION_RESULTS.json'
 if result.exists():RESULT['admission']=json.loads(result.read_bytes())
 RESULT['status']='PASS' if p.returncode==0 and RESULT.get('admission',{}).get('status')=='PASS' else 'CPU_INTEGRATION_BLOCKED'
 if RESULT['status']=='PASS':
  with (RUN_DIR/'replay-worker.log').open('w') as log:
   replay=subprocess.run([sys.executable,str(study/'cpu_worker_replay.py'),str(RUN_DIR/'replay')],stdout=log,stderr=subprocess.STDOUT,timeout=1200)
  contract=RUN_DIR/'replay/CPU_REPLAY_CONTRACT.json'
  RESULT['plumbing_replay']=json.loads(contract.read_bytes()) if contract.exists() else None
  if replay.returncode or not RESULT['plumbing_replay'] or RESULT['plumbing_replay']['status']!='PASS_PLUMBING_ONLY':RESULT['status']='CPU_REPLAY_BLOCKED'
except BaseException as e:
 RESULT.update(status='CPU_INTEGRATION_BLOCKED',error_type=type(e).__name__,reason=str(e),traceback=traceback.format_exc())
finally:
 (RUN_DIR/'CPU_ADMISSION_SUMMARY.json').write_text(json.dumps(RESULT,indent=2))
 archive=shutil.make_archive(str(RUN_DIR),'zip',RUN_DIR)
 print('R2A_CPU_ADMISSION',json.dumps(RESULT),flush=True)
 print('EVIDENCE_ARCHIVE',archive,flush=True)
'''
compile(code,'cpu-notebook','exec')
nb=dict(nbformat=4,nbformat_minor=5,metadata=dict(kernelspec=dict(name='python3',language='python',display_name='Python 3')),cells=[dict(cell_type='code',execution_count=None,id='r2acpu',metadata={},outputs=[],source=code)])
folder=D/'cpu-notebook';folder.mkdir(exist_ok=True)
(folder/'study.ipynb').write_text(json.dumps(nb,indent=1)+'\n')
meta=json.loads((ROOT/'work/gemma-r12-01/authorized-gpu-02/kernel-metadata.json').read_bytes())
meta.update(id='wudangdexiaodoashi/r2a-native-cpu-admission-01',title='R2A Native CPU Admission 01',enable_gpu=False,model_sources=[])
meta['enable_internet']=True
meta.pop('machine_shape',None)
meta['dataset_sources'].append(metadata['id'])
(folder/'kernel-metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
assert len((folder/'study.ipynb').read_bytes())<1_000_000
print(json.dumps(dict(bundle_bytes=bundle.stat().st_size,bundle_sha256=manifest['bundle_sha256'],cpu_notebook=str(folder),metadata=meta)))
