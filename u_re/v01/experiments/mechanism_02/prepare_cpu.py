"""CPU-only build; no GPU Notebook generation or GPU launch path exists."""
import ast
import base64
import io
import json
from pathlib import Path
import subprocess
import zipfile
from u_re.v01.build import ROOT,archive,sha,write

HERE=Path(__file__).resolve().parent
FREEZE='ac20c4745027c6068571292898b45c4ea0cfb630'


def build():
    for name in ('select.py','screen.py','SELECTION_PROTOCOL.json','RANKED_POOL.json','EXCLUSION_LEDGER_V02.json','TASK_POOL_METADATA.json'):
        raw=subprocess.check_output(['git','show',FREEZE+':'+(HERE/name).relative_to(ROOT).as_posix()],cwd=ROOT)
        assert (HERE/name).read_bytes()==raw,'Frozen policy changed: '+name
    nb=json.loads((ROOT/'u_re/v01/notebooks/cpu03/study.ipynb').read_text())
    setup=nb['cells'][0]['source']
    line=next(s for s in setup.splitlines() if s.startswith("payload=__import__('base64').b64decode("))
    value=ast.literal_eval(line[len("payload=__import__('base64').b64decode("):-1])
    with zipfile.ZipFile(io.BytesIO(base64.b64decode(value))) as z:
        assert z.testzip() is None;files={n:z.read(n) for n in z.namelist()}
    for p in [*HERE.glob('*.py'),*(HERE/'tests').glob('*.py')]:files[p.relative_to(ROOT).as_posix()]=p.read_bytes()
    for n in ('SELECTION_PROTOCOL.json','RANKED_POOL.json','EXCLUSION_LEDGER_V02.json','TASK_POOL_METADATA.json'):
        p=HERE/n;files[p.relative_to(ROOT).as_posix()]=p.read_bytes()
    reg=dict(experiment_id='U-RE-V01-MECHANISM-02',selection_commit=FREEZE,GPU=False,model_inference=False,
             source_hashes={n:sha(b) for n,b in files.items()},max_checks=8,
             pool_diversity_observed=1,promotion_blocked_before_CPU=True,
             scope='Prospective bounded evaluator-only baseline screening; cannot promote a one-repository pool. No model/Agent/reference repair.')
    write(HERE/'registrations/cpu01.json',(json.dumps(reg,indent=2)+'\n').encode())
    prefix=HERE.relative_to(ROOT).as_posix()
    files[prefix+'/runtime_registration.json']=(HERE/'registrations/cpu01.json').read_bytes()
    payload=archive(files)
    start=setup.index("payload=__import__('base64').b64decode(");end=setup.index('with zipfile.ZipFile',start)
    setup=setup[:start]+"payload=__import__('base64').b64decode("+repr(base64.b64encode(payload).decode())+")\nassert hashlib.sha256(payload).hexdigest()=="+repr(sha(payload))+"\n"+setup[end:]
    setup=setup.replace("Path('/kaggle/working/u_re_v01')/'cpu03'/","Path('/kaggle/working/u_re_mechanism02')/'cpu01'/")
    setup+='\nM02=json.loads((SOURCE/'+repr(prefix+'/runtime_registration.json')+').read_text())\nassert M02["GPU"] is False\nfor n,h in M02["source_hashes"].items():assert hashlib.sha256((SOURCE/n).read_bytes()).hexdigest()==h,n\n'
    from s1.prepare import INSTALL,IMAGE
    execute=INSTALL+"\nwith (RUN_DIR/'cpu.log').open('x') as log:\n    result=subprocess.run([sys.executable,'-m','u_re.v01.experiments.mechanism_02.screen',str(RUN_DIR/'validation')],cwd=SOURCE,stdout=log,stderr=subprocess.STDOUT,timeout=6000)\nprint('SCREEN_CPU_EXIT',result.returncode,flush=True)\nassert result.returncode==0,'Preserve CPU screening exception'\n"
    code="from harness_v2.evidence import bundle\ntry:\n"+''.join('    '+l+'\n' for l in execute.splitlines())+"finally:print('SCREEN_EVIDENCE',bundle(RUN_DIR),flush=True)\n"
    cells=[]
    for s in (setup,code):
        compile(s,'<CPU screening>','exec',flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
        cells.append(dict(cell_type='code',metadata={},source=s,outputs=[],execution_count=None,id=sha(s.encode())[:12]))
    raw=(json.dumps(dict(cells=cells,metadata=nb['metadata'],nbformat=4,nbformat_minor=5),indent=1)+'\n').encode()
    meta=dict(id='wudangdexiaodoashi/gemma4-u-re-mechanism02-screen-cpu01',title='gemma4-u-re-mechanism02-screen-cpu01',code_file='study.ipynb',
        language='python',kernel_type='notebook',is_private=True,enable_gpu=False,enable_tpu=False,enable_internet=False,
        competition_sources=['gemma-4-developer-agent'],dataset_sources=['metric/gemma-4-developer-agent-wheelhouse'],
        model_sources=[],kernel_sources=[],docker_image=IMAGE,docker_image_pinning_type='original')
    write(HERE/'notebooks/cpu01/study.ipynb',raw)
    write(HERE/'notebooks/cpu01/kernel-metadata.json',(json.dumps(meta,indent=2)+'\n').encode())
    freeze=dict(kernel=meta['id'],GPU=False,selection_commit=FREEZE,notebook_sha256=sha(raw),payload_sha256=sha(payload),
        metadata_sha256=sha((HERE/'notebooks/cpu01/kernel-metadata.json').read_bytes()),
        requested_CPU_window_seconds=7200,worker_deadline_seconds=6000,baseline_verification_seconds=300)
    write(HERE/'registrations/cpu01_build.json',(json.dumps(freeze,indent=2)+'\n').encode())
    print(json.dumps(freeze,indent=2))


if __name__=='__main__':build()
