"""Seal the exact CPU entry and inherited source closure, no GPU/model inputs."""
import base64
import io
import json
import zipfile

from meer.v01.build import archive
from s1.prepare import INSTALL,IMAGE
from .prepare import HERE,ROOT,PRIVATE,REF,sha,write,freeze


def build(version=1):
    assert version in (1,2)
    freeze()
    previous=ROOT/'egrd/v023/cpu-v1'
    manifest=json.loads((previous/'BUILD.json').read_bytes())
    old=(previous/'payload.zip').read_bytes();assert sha(old)==manifest['payload_sha256']
    with zipfile.ZipFile(io.BytesIO(old)) as z:
        assert z.testzip() is None
        files={n:z.read(n) for n in z.namelist() if n!='recovery_registration.json'}
    for name in ('__init__.py','prepare.py','scripted_boundary.py','sandbox_adapter.py','device_runtime.py','development_evaluator.py','cpu_preflight.py',
                 'TASK_IDENTITY_LOCK.json','S0_AGENT_LOCK.json','EVIDENCE_RECEIPT.json'):
        files['egrd/v031/'+name]=(HERE/name).read_bytes()
    for name in ('__init__.py','runtime.py','DATASET_BUILD_V1.json'):
        files['egrd/v03/'+name]=(ROOT/'egrd/v03'/name).read_bytes()
    files['egrd/v023/RECOVERED_DEPENDENCY_IDENTITIES.json']=(ROOT/'egrd/v023/RECOVERED_DEPENDENCY_IDENTITIES.json').read_bytes()
    files['candidates/s0/submission.zip']=(ROOT/'candidates/s0/submission.zip').read_bytes()
    for name in ('original_task.json','regression.py'):
        files['egrd/v031/private/'+name]=(PRIVATE/name).read_bytes()
    reg=dict(files={n:sha(b) for n,b in files.items()},wheel_hashes=manifest['wheel_hashes'],
        CPU_MODEL='SCRIPTED_ONLY',entry='egrd.v031.cpu_preflight.run',GPU=False)
    files['v031_registration.json']=(json.dumps(reg,indent=2)+'\n').encode()
    payload=archive(files)
    folder=PRIVATE/f'notebook-v{version}';folder.mkdir(parents=True,exist_ok=False)
    (folder/'payload.zip').write_bytes(payload)
    setup=f'''import os,sys,json,hashlib,zipfile,io,subprocess,shutil,time
from pathlib import Path
RUN_DIR=Path('/kaggle/working/egrd-v031-cpu-v{version}')
RUN_DIR.mkdir(parents=True,exist_ok=False)
SOURCE=RUN_DIR/'source'
raw=base64_payload=__import__('base64').b64decode({base64.b64encode(payload).decode()!r})
assert hashlib.sha256(raw).hexdigest()=={sha(payload)!r}
with zipfile.ZipFile(io.BytesIO(raw)) as z:
 assert z.testzip() is None
 assert all(not n.startswith('/') and '..' not in Path(n).parts for n in z.namelist())
 z.extractall(SOURCE)
sys.path.insert(0,str(SOURCE))
REG=json.loads((SOURCE/'v031_registration.json').read_bytes())
for name,digest in REG['files'].items():assert hashlib.sha256((SOURCE/name).read_bytes()).hexdigest()==digest,name
WHEELHOUSE_DIR=next(Path('/kaggle/input').rglob('swegemma-0.2.11-py3-none-any.whl')).parent
actual={{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in WHEELHOUSE_DIR.glob('*.whl') if 'cutlass' not in p.name.lower()}}
assert actual==REG['wheel_hashes']
(RUN_DIR/'PAYLOAD_IDENTITY.json').write_text(json.dumps(dict(payload_sha256={sha(payload)!r},files=REG['files'])))
'''
    body=INSTALL+'''
try:
 with (RUN_DIR/'cpu.log').open('x') as log:
  result=subprocess.run([sys.executable,'-m','egrd.v031.cpu_preflight',str(RUN_DIR/'results')],cwd=SOURCE,
   stdout=log,stderr=subprocess.STDOUT,timeout=2400)
 assert result.returncode==0,'Preserve the original CPU error; no blind retry'
finally:
 from harness_v2.evidence import bundle
 print('EGRD_V031_CPU_EVIDENCE',bundle(RUN_DIR),flush=True)
'''
    for text in (setup,body):compile(text,'<cpu-notebook>','exec')
    nb=dict(nbformat=4,nbformat_minor=5,metadata=dict(kernelspec=dict(name='python3',language='python',display_name='Python 3')),
        cells=[dict(cell_type='code',source=t,id=sha(t.encode())[:12],metadata={},outputs=[],execution_count=None) for t in (setup,body)])
    raw=(json.dumps(nb,indent=1)+'\n').encode();(folder/'study.ipynb').write_bytes(raw)
    meta=dict(id=REF,title='EGRD V031 Evidence to Patch CPU',code_file='study.ipynb',language='python',kernel_type='notebook',
        is_private=True,enable_gpu=False,enable_tpu=False,enable_internet=False,machine_shape='',
        competition_sources=[],dataset_sources=['metric/gemma-4-developer-agent-wheelhouse','wudangdexiaodoashi/egrd-repair-development'],
        kernel_sources=[],model_sources=[],docker_image=IMAGE,docker_image_pinning_type='original')
    write(folder/'kernel-metadata.json',meta)
    write(HERE/f'CPU_BUILD_V{version}.json',dict(Notebook_ref=REF,version=version,Notebook_sha256=sha(raw),
        payload_sha256=sha(payload),members=reg['files'],wheel_hashes=reg['wheel_hashes'],
        CPU_MODEL='SCRIPTED_ONLY',GPU=False,base_commit='5829838066b5c3cfb3037ebbf2613011c2d4f214'))
    print('CPU payload frozen',sha(payload),'; no dispatch.')


if __name__=='__main__':
    import sys
    build(int(sys.argv[1]) if len(sys.argv)>1 else 1)
