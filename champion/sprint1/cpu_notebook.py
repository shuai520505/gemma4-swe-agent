"""Upload packaging only; computation runs on one private CPU Kaggle Notebook."""
import base64
import io
import json
import zipfile
from .build import ROOT,HERE,PRIVATE,sha,write
from meer.v01.build import archive
from s1.prepare import IMAGE,INSTALL

REF='wudangdexiaodoashi/champion-sprint1-cpu-review'

def build():
    old=json.loads((ROOT/'egrd/v0311/CPU_BUILD.json').read_bytes())
    raw=(ROOT.parent/'private-evidence/egrd_v0311/notebook-v1/payload.zip').read_bytes()
    assert sha(raw)==old['payload_sha256']
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        files={n:z.read(n) for n in z.namelist() if n!='v0311_registration.json'}
    files['champion/__init__.py']=b''
    for name in ('__init__.py','build.py','kaggle_cpu.py','C1_BUDGET.md','C3_TEST_AWARE.md','CANDIDATE_MANIFEST.json'):
        files['champion/sprint1/'+name]=(HERE/name).read_bytes()
    for name in ('__init__.py','data.py','source_observer.py','evaluate.py'):
        files['egrd/v032/'+name]=(ROOT/'egrd/v032'/name).read_bytes()
    files['egrd/v023/RECOVERED_DEPENDENCY_IDENTITIES.json']=(ROOT/'egrd/v023/RECOVERED_DEPENDENCY_IDENTITIES.json').read_bytes()
    prior=json.loads((ROOT/'egrd/v032/RAW_ARCHIVES.json').read_bytes())['archive']
    with zipfile.ZipFile(prior['private_path']) as z:
        files['champion/sprint1/private/original_fallback.patch']=z.read('execution/A/unsubmitted_fallback.patch')
    registration=dict(files={n:sha(b) for n,b in files.items()},wheel_hashes=old['wheel_hashes'])
    files['champion_registration.json']=(json.dumps(registration,indent=2)+'\n').encode()
    payload=archive(files);folder=PRIVATE/'kaggle-cpu-v1';folder.mkdir(parents=True,exist_ok=False)
    setup=f'''import os,sys,json,hashlib,zipfile,io,subprocess,shutil,time
from pathlib import Path
RUN_DIR=Path('/kaggle/working/champion-sprint1-cpu');RUN_DIR.mkdir(parents=True,exist_ok=False)
SOURCE=RUN_DIR/'source'
raw=__import__('base64').b64decode({base64.b64encode(payload).decode()!r})
assert hashlib.sha256(raw).hexdigest()=={sha(payload)!r}
with zipfile.ZipFile(io.BytesIO(raw)) as z:
 assert z.testzip() is None and all(not n.startswith('/') and '..' not in Path(n).parts for n in z.namelist())
 z.extractall(SOURCE)
sys.path.insert(0,str(SOURCE))
REG=json.loads((SOURCE/'champion_registration.json').read_bytes())
for n,h in REG['files'].items():assert hashlib.sha256((SOURCE/n).read_bytes()).hexdigest()==h,n
(RUN_DIR/'PAYLOAD_IDENTITY.json').write_text(json.dumps(dict(payload_sha256={sha(payload)!r},files=REG['files'])))
WHEELHOUSE_DIR=next(p for p in Path('/kaggle/input').rglob('swegemma-0.2.11-py3-none-any.whl') if 'gemma-4-developer-agent-wheelhouse' in str(p)).parent
actual={{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in WHEELHOUSE_DIR.glob('*.whl') if 'cutlass' not in p.name.lower()}}
assert actual==REG['wheel_hashes']
'''
    body='try:\n'+'\n'.join(' '+line for line in (INSTALL+'''
with (RUN_DIR/'cpu.log').open('x') as log:
 result=subprocess.run([sys.executable,'-m','champion.sprint1.kaggle_cpu',str(RUN_DIR/'validation')],cwd=SOURCE,stdout=log,stderr=subprocess.STDOUT,timeout=1800)
assert result.returncode==0,'CPU task failed; preserve original evidence, never auto-redispatch'
''').splitlines())+'''
finally:
 from harness_v2.evidence import bundle
 print('CHAMPION_CPU_ARCHIVE',bundle(RUN_DIR),flush=True)
'''
    nb=dict(nbformat=4,nbformat_minor=5,metadata=dict(kernelspec=dict(name='python3',language='python',display_name='Python 3')),
        cells=[dict(cell_type='code',source=s,id=sha(s.encode())[:12],metadata={},outputs=[],execution_count=None) for s in (setup,body)])
    (folder/'study.ipynb').write_text(json.dumps(nb,indent=1)+'\n',encoding='utf8',newline='\n')
    meta=dict(id=REF,title='Champion Sprint1 CPU Review',code_file='study.ipynb',language='python',kernel_type='notebook',
        is_private=True,enable_gpu=False,enable_tpu=False,enable_internet=False,machine_shape='',model_sources=[],
        competition_sources=[],dataset_sources=['metric/gemma-4-developer-agent-wheelhouse','wudangdexiaodoashi/egrd-repair-development'],
        kernel_sources=[],docker_image=IMAGE,docker_image_pinning_type='original')
    write(folder/'kernel-metadata.json',meta)
    write(HERE/'CPU_BUILD.json',dict(ref=REF,CPU_only=True,Notebook_sha256=sha((folder/'study.ipynb').read_bytes()),
        payload_sha256=sha(payload),members=registration['files'],wheel_hashes=old['wheel_hashes'],max_dispatches=1,
        authority='Human latest instruction: 不要在本地上搞啊，你kaggle和github上面搞; CPU computation moved to Kaggle, no GPU/inference/submission'))
    print('Prepared private CPU-only transfer payload',sha(payload))

if __name__=='__main__':build()
