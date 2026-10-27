"""Build once: exact private CPU payload, genuine device gate before SDK install."""
import base64
import io
import json
import zipfile

from meer.v01.build import archive
from s1.prepare import INSTALL, IMAGE
from .prepare import HERE, OLD, ROOT, PRIVATE, PRIOR, REF, BASE, sha, write, verify_history


def build():
    verify_history()
    previous = ROOT / 'egrd/v023/cpu-v1'
    manifest = json.loads((previous / 'BUILD.json').read_bytes())
    raw = (previous / 'payload.zip').read_bytes()
    assert sha(raw) == manifest['payload_sha256']
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        assert z.testzip() is None
        files = {n: z.read(n) for n in z.namelist() if n != 'recovery_registration.json'}
    for name in ('__init__.py', 'prepare.py', 'device_runtime.py', 'sandbox_adapter.py',
                 'TASK_IDENTITY_LOCK.json', 'S0_AGENT_LOCK.json', 'EVIDENCE_RECEIPT.json'):
        files['egrd/v031/' + name] = (OLD / name).read_bytes()
    for name in ('__init__.py', 'device_gate.py', 'lifecycle.py', 'sandbox_adapter.py',
                 'scripted_boundary.py', 'boundary_audit.py', 'development_evaluator.py', 'cpu_preflight.py'):
        files['egrd/v0311/' + name] = (HERE / name).read_bytes()
    for name in ('__init__.py', 'runtime.py', 'DATASET_BUILD_V1.json'):
        files['egrd/v03/' + name] = (ROOT / 'egrd/v03' / name).read_bytes()
    files['egrd/v023/RECOVERED_DEPENDENCY_IDENTITIES.json'] = (ROOT / 'egrd/v023/RECOVERED_DEPENDENCY_IDENTITIES.json').read_bytes()
    files['candidates/s0/submission.zip'] = (ROOT / 'candidates/s0/submission.zip').read_bytes()
    for name in ('original_task.json', 'regression.py'):
        files['egrd/v031/private/' + name] = (PRIOR / name).read_bytes()
    for name, body in files.items():
        if name.endswith('.py'):
            compile(body, name, 'exec')
    reg = dict(files={n: sha(b) for n, b in files.items()}, wheel_hashes=manifest['wheel_hashes'],
               CPU_MODEL='SCRIPTED_ONLY', entry='egrd.v0311.cpu_preflight.run', GPU=False)
    files['v0311_registration.json'] = (json.dumps(reg, indent=2) + '\n').encode()
    payload = archive(files)
    folder = PRIVATE / 'notebook-v1'
    folder.mkdir(parents=True, exist_ok=False)
    (folder / 'payload.zip').write_bytes(payload)
    setup = f'''import os,sys,json,hashlib,zipfile,io,subprocess,shutil,time
from pathlib import Path
RUN_DIR=Path('/kaggle/working/egrd-v0311-cpu-v1')
RUN_DIR.mkdir(parents=True,exist_ok=False)
SOURCE=RUN_DIR/'source'
raw=__import__('base64').b64decode({base64.b64encode(payload).decode()!r})
assert hashlib.sha256(raw).hexdigest()=={sha(payload)!r}
with zipfile.ZipFile(io.BytesIO(raw)) as z:
 assert z.testzip() is None
 assert all(not n.startswith('/') and '..' not in Path(n).parts for n in z.namelist())
 z.extractall(SOURCE)
sys.path.insert(0,str(SOURCE))
REG=json.loads((SOURCE/'v0311_registration.json').read_bytes())
for name,digest in REG['files'].items():assert hashlib.sha256((SOURCE/name).read_bytes()).hexdigest()==digest,name
(RUN_DIR/'PAYLOAD_IDENTITY.json').write_text(json.dumps(dict(payload_sha256={sha(payload)!r},files=REG['files'])))
'''
    work = '''from egrd.v0311.device_gate import run as check_device
check_device(RUN_DIR)
WHEELHOUSE_DIR=next(Path('/kaggle/input').rglob('swegemma-0.2.11-py3-none-any.whl')).parent
actual={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in WHEELHOUSE_DIR.glob('*.whl') if 'cutlass' not in p.name.lower()}
assert actual==REG['wheel_hashes']
'''+INSTALL+'''
with (RUN_DIR/'cpu.log').open('x') as log:
 result=subprocess.run([sys.executable,'-m','egrd.v0311.cpu_preflight',str(RUN_DIR/'results')],cwd=SOURCE,
  stdout=log,stderr=subprocess.STDOUT,timeout=2400)
assert result.returncode==0,'Preserve CPU failure; no corrective execution authorized'
'''
    body = 'try:\n' + '\n'.join(' '+line for line in work.splitlines()) + '''
except BaseException as exc:
 (RUN_DIR/'EXECUTION_FAILURE.json').write_text(json.dumps(dict(type=type(exc).__name__,error=str(exc),
  errno=getattr(exc,'errno',None),GPU=0,real_Gemma_requests=0,automatic_retry=False)))
 raise
finally:
 from harness_v2.evidence import bundle
 print('EGRD_V0311_CPU_EVIDENCE',bundle(RUN_DIR),flush=True)
'''
    for cell in (setup, body):
        compile(cell, '<sealed-cpu-notebook>', 'exec')
    nb = dict(nbformat=4, nbformat_minor=5, metadata=dict(kernelspec=dict(name='python3', language='python', display_name='Python 3')),
              cells=[dict(cell_type='code', source=c, id=sha(c.encode())[:12], metadata={}, outputs=[], execution_count=None) for c in (setup, body)])
    encoded = (json.dumps(nb, indent=1) + '\n').encode()
    (folder / 'study.ipynb').write_bytes(encoded)
    meta = dict(id=REF, title='EGRD V0311 CPU Runner Recovery', code_file='study.ipynb', language='python', kernel_type='notebook',
                is_private=True, enable_gpu=False, enable_tpu=False, enable_internet=False, machine_shape='',
                competition_sources=[], dataset_sources=['metric/gemma-4-developer-agent-wheelhouse', 'wudangdexiaodoashi/egrd-repair-development'],
                kernel_sources=[], model_sources=[], docker_image=IMAGE, docker_image_pinning_type='original')
    write(folder / 'kernel-metadata.json', meta)
    write(HERE / 'CPU_BUILD.json', dict(Notebook_ref=REF, Notebook_sha256=sha(encoded), metadata_sha256=sha((folder/'kernel-metadata.json').read_bytes()),
          payload_sha256=sha(payload), members=reg['files'], wheel_hashes=reg['wheel_hashes'], CPU_MODEL='SCRIPTED_ONLY',
          GPU=False, base_commit=BASE, max_dispatches=1, dataset_expected_version=2))
    print('Frozen CPU payload:', sha(payload), '; NOT_DISPATCHED')


if __name__ == '__main__':
    build()
