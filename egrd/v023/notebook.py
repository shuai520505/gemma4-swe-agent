"""CPU-only closure from a verified historical payload; no model inputs."""
import base64
import io
import json
from pathlib import Path
import zipfile

from meer.v01.build import archive
from .cli_recovery import HERE, ROOT, PRIVATE, REF, sha


def build(version=1):
    assert version in (1,2)
    old=ROOT/'meer/v01/cpu03'
    previous=json.loads((old/'BUILD.json').read_bytes())
    raw=(old/'payload.zip').read_bytes()
    assert sha(raw)==previous['payload_sha256']
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        assert z.testzip() is None
        files={n:z.read(n) for n in z.namelist() if n!='gpu_registration.json'}
    # All inherited source files retain their exact bytes; only the new entry
    # and the exact frozen N/D ZIPs are added. No task/snapshot/model is bundled.
    for name in ('__init__.py','cpu_acceptance.py'):
        files['egrd/v023/'+name]=(HERE/name).read_bytes()
    files.setdefault('egrd/__init__.py',b'')
    for arm in ('N','D'):
        files[f'egrd/v022/submission_{arm}.zip']=(ROOT/f'egrd/v022/submission_{arm}.zip').read_bytes()
    files['meer/v01/OFFICIAL_SOURCE_PINS.json']=(ROOT/'meer/v01/OFFICIAL_SOURCE_PINS.json').read_bytes()
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        wheel_hashes=json.loads(z.read('gpu_registration.json'))['wheel_hashes']
    reg=dict(files={n:sha(b) for n,b in files.items()},wheel_hashes=wheel_hashes,
        production_entry='egrd.v023.cpu_acceptance.run',CPU_MODEL='SCRIPTED_ONLY',GPU=False)
    files['recovery_registration.json']=(json.dumps(reg,indent=2)+'\n').encode()
    payload=archive(files)
    target=HERE/f'cpu-v{version}'
    target.mkdir(parents=True,exist_ok=False)
    (target/'payload.zip').write_bytes(payload)
    setup=f'''import os,sys,json,hashlib,zipfile,io,subprocess,shutil,time
from pathlib import Path
RUN_DIR=Path('/kaggle/working/egrd-v023-cpu-v{version}')
RUN_DIR.mkdir(parents=True,exist_ok=False)
SOURCE=RUN_DIR/'source'
raw=__import__('base64').b64decode({base64.b64encode(payload).decode()!r})
assert hashlib.sha256(raw).hexdigest()=={sha(payload)!r}
with zipfile.ZipFile(io.BytesIO(raw)) as z:
    assert z.testzip() is None
    assert all(not n.startswith('/') and '..' not in Path(n).parts for n in z.namelist())
    z.extractall(SOURCE)
sys.path.insert(0,str(SOURCE))
REG=json.loads((SOURCE/'recovery_registration.json').read_bytes())
for name,digest in REG['files'].items():assert hashlib.sha256((SOURCE/name).read_bytes()).hexdigest()==digest,name
WHEELHOUSE_DIR=next(Path('/kaggle/input').rglob('swegemma-0.2.11-py3-none-any.whl')).parent
actual={{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in WHEELHOUSE_DIR.glob('*.whl') if 'cutlass' not in p.name.lower()}}
assert actual==REG['wheel_hashes'],'Pinned wheelhouse differs'
(RUN_DIR/'WHEEL_HASHES.json').write_text(json.dumps(actual,indent=2))
(RUN_DIR/'PAYLOAD_IDENTITY.json').write_text(json.dumps(dict(payload_sha256={sha(payload)!r},files=REG['files'])))
'''
    from s1.prepare import INSTALL, IMAGE
    body=INSTALL+'''
try:
    with (RUN_DIR/'cpu.log').open('x') as log:
        result=subprocess.run([sys.executable,'-m','egrd.v023.cpu_acceptance',str(RUN_DIR/'validation')],cwd=SOURCE,stdout=log,stderr=subprocess.STDOUT,timeout=2400)
    assert result.returncode==0,'CPU acceptance failed; preserve original log'
finally:
    from harness_v2.evidence import bundle
    print('EGRD_V023_CPU_EVIDENCE',bundle(RUN_DIR),flush=True)
'''
    for code in (setup,body):compile(code,'<cpu-only>','exec')
    nb=dict(nbformat=4,nbformat_minor=5,metadata=dict(kernelspec=dict(name='python3',language='python',display_name='Python 3')),
        cells=[dict(cell_type='code',source=c,id=sha(c.encode())[:12],metadata={},outputs=[],execution_count=None) for c in (setup,body)])
    nbraw=(json.dumps(nb,indent=1)+'\n').encode()
    (target/'study.ipynb').write_bytes(nbraw)
    meta=dict(id=REF,title='EGRD V023 Compiler CPU Recovery',code_file='study.ipynb',language='python',
        kernel_type='notebook',is_private=True,enable_gpu=False,enable_tpu=False,enable_internet=False,
        machine_shape='',competition_sources=['gemma-4-developer-agent'],
        dataset_sources=['metric/gemma-4-developer-agent-wheelhouse'],model_sources=[],kernel_sources=[],
        docker_image=IMAGE,docker_image_pinning_type='original')
    (target/'kernel-metadata.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf8',newline='\n')
    (target/'BUILD.json').write_text(json.dumps(dict(version=version,ref=REF,Notebook_sha256=sha(nbraw),
        payload_sha256=sha(payload),payload_members=reg['files'],wheel_hashes=wheel_hashes,
        source_base='e11b28c99bec91049aec68119fead5e13fa68373',CPU_MODEL='SCRIPTED_ONLY',
        CPU_only=True,model_sources=[],actual_Gemma_calls=0),indent=2)+'\n',encoding='utf8',newline='\n')
    print('Frozen CPU payload',sha(payload),len(reg['files']),'members; no dispatch.')


if __name__=='__main__':
    import sys
    build(int(sys.argv[1]) if len(sys.argv)>1 else 1)
