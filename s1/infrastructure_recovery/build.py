"""CPU-only builder; this module has no GPU or submission path."""
import ast
import base64
import json
from pathlib import Path
from s1.prepare import INSTALL,IMAGE
from s1.util import sha,sha_file,save,archive
from experiments.prepare import write_new

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent


def build(revision,mode):
    reg=json.loads((ROOT/'s1/experiments/e1_outputcap_smoke_02/registration.json').read_text())
    original=ROOT/'s1/experiments/e1_outputcap_smoke_02/_local/cpu-extract/source'
    files={n:(original/n).read_bytes() for n in reg['source_hashes']}
    assert all(sha(b)==reg['source_hashes'][n] for n,b in files.items())
    for p in HERE.rglob('*.py'):
        if not {'_local','results','__pycache__'}.intersection(p.relative_to(HERE).parts):
            files[p.relative_to(ROOT).as_posix()]=p.read_bytes()
    for name in ('upstream_blob_pins.json','next_experiment_plan.json'):
        if (HERE/name).exists():files[(HERE/name).relative_to(ROOT).as_posix()]=(HERE/name).read_bytes()
    reg=dict(reg,revision=revision,infrastructure_recovery=True,mode=mode,
        source_hashes={n:sha(b) for n,b in sorted(files.items())})
    save(HERE/f'registrations/{revision}.json',reg)
    files['s1/registration.json']=(HERE/f'registrations/{revision}.json').read_bytes()
    payload=archive(files)
    setup=f'''import os,sys,json,hashlib,zipfile,io,subprocess,shutil,time
SESSION_STARTED=time.monotonic()
from pathlib import Path
from datetime import datetime,timezone
RUN_DIR=Path('/kaggle/working/s1_infra_recovery')/{revision!r}/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
RUN_DIR.mkdir(parents=True,exist_ok=False)
SOURCE=RUN_DIR/'source'
payload=__import__('base64').b64decode({base64.b64encode(payload).decode()!r})
assert hashlib.sha256(payload).hexdigest()=={sha(payload)!r}
with zipfile.ZipFile(io.BytesIO(payload)) as z:
    assert z.testzip() is None
    assert all(not n.startswith('/') and '..' not in Path(n).parts for n in z.namelist())
    z.extractall(SOURCE)
sys.path.insert(0,str(SOURCE))
REG=json.loads((SOURCE/'s1/registration.json').read_text())
for n,h in REG['source_hashes'].items():assert hashlib.sha256((SOURCE/n).read_bytes()).hexdigest()==h,n
WHEELHOUSE_DIR=next(Path('/kaggle/input').rglob('swegemma-0.2.11-py3-none-any.whl')).parent
actual={{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in WHEELHOUSE_DIR.glob('*.whl') if 'cutlass' not in p.name.lower()}}
assert actual==REG['wheel_hashes'],'Official wheel drift'
(RUN_DIR/'wheel_hashes.json').write_text(json.dumps(actual,indent=2))
'''
    if mode=='diagnose':
        commands="p=subprocess.run([sys.executable,'-m','s1.infrastructure_recovery.diagnose',str(RUN_DIR/'diagnostics')],cwd=SOURCE,capture_output=True,text=True,timeout=1200)\n"
    else:
        commands="p=subprocess.run([sys.executable,'-m','s1.infrastructure_recovery.cpu',str(RUN_DIR/'validation')],cwd=SOURCE,capture_output=True,text=True,timeout=1800)\n"
    commands+="(RUN_DIR/'runner.stdout.log').write_text(p.stdout);(RUN_DIR/'runner.stderr.log').write_text(p.stderr)\nprint(p.stdout+p.stderr,flush=True)\nassert p.returncode==0,'CPU investigation/gate failed'\n"
    run='from harness_v2.evidence import bundle\ntry:\n'+''.join('    '+line+'\n' for line in (INSTALL+'\n'+commands).splitlines())+"finally:print('INFRA_CPU_EVIDENCE',bundle(RUN_DIR),flush=True)\n"
    cells=[]
    for code in (setup,run):
        compile(code,'<cpu-notebook>','exec',flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
        cells.append(dict(cell_type='code',metadata={},source=code,outputs=[],execution_count=None,id=sha(code.encode())[:12]))
    raw=(json.dumps(dict(cells=cells,metadata=dict(kernelspec=dict(display_name='Python 3',language='python',name='python3')),nbformat=4,nbformat_minor=5),indent=1)+'\n').encode()
    path=HERE/'notebooks'/revision
    write_new(path/'study.ipynb',raw)
    slug='gemma4-s1-infra-'+revision+'-cpu'
    save(path/'kernel-metadata.json',dict(id='wudangdexiaodoashi/'+slug,title=slug,code_file='study.ipynb',language='python',kernel_type='notebook',
        is_private=True,enable_gpu=False,enable_tpu=False,enable_internet=False,
        competition_sources=['gemma-4-developer-agent'],dataset_sources=['metric/gemma-4-developer-agent-wheelhouse'],
        model_sources=[],kernel_sources=[],docker_image=IMAGE,docker_image_pinning_type='original'))
    save(HERE/f'registrations/{revision}-notebook.json',dict(notebook_sha256=sha(raw),payload_sha256=sha(payload),GPU=False,mode=mode))
    print(path)


if __name__=='__main__':
    import sys
    build(sys.argv[1],sys.argv[2])
