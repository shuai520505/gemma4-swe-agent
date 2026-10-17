"""Immutable C1 derivation and new exploratory B/C1 study, no submission action."""
import ast
import base64
import difflib
import hashlib
import json
from pathlib import Path
from cure.build import AGENT_FILES, archive, write_new
from cure.runner import require_gate
from . import EXPERIMENT

REPO=Path(__file__).resolve().parents[2]
STUDY=REPO/'cure/gpu-study-02-c1'

def sha(raw):return hashlib.sha256(raw).hexdigest()
def save(path,obj):write_new(path,(json.dumps(obj,indent=2)+'\n').encode())


def derive():
    old=REPO/'cure/candidates/cure_v01';new=REPO/'cure/candidates/cure_v01_c1'
    before=(old/'prompts/system.md').read_bytes()
    assert before.count(b'<cure>{JSON}</cure>')==1
    after=before.replace(b'<cure>{JSON}</cure>',b'<cure>JSON object</cure>')
    for name in AGENT_FILES:write_new(new/name,after if name=='prompts/system.md' else (old/name).read_bytes())
    data=archive({n:(new/n).read_bytes() for n in AGENT_FILES})
    write_new(REPO/'cure/packages/cure_v01_c1/submission.zip',data)
    diff=''.join(difflib.unified_diff(before.decode().splitlines(keepends=True),after.decode().splitlines(keepends=True),
        fromfile='frozen-cure_v01/prompts/system.md',tofile='cure_v01_c1/prompts/system.md'))
    write_new(STUDY/'candidate-exact.diff',diff.encode())
    record=dict(candidate='C1',kind='compatibility_only',old_prompt_sha256=sha(before),new_prompt_sha256=sha(after),
        old_zip_sha256=sha((REPO/'cure/packages/cure_v01/submission.zip').read_bytes()),new_zip_sha256=sha(data),
        zip_bytes=len(data),members={n:sha((new/n).read_bytes()) for n in AGENT_FILES},
        only_change='Literal <cure>{JSON}</cure> -> <cure>JSON object</cure>; no other Prompt/config change',
        internal_agent_name_unchanged=True)
    save(STUDY/'candidate-derivation.json',record)
    return record


def derive_session():
    original=(REPO/'cure/gpu_mechanism/session.py').read_text(encoding='utf-8')
    text=original.replace('from .audit import inspect_run','from cure.gpu_mechanism.audit import inspect_run')
    start=text.index("    if batch!='smoke':")
    end=text.index('    limits,constraints=',start)
    text=text[:start]+"    assert identity==plan['expected_model_files'],'Pinned model bytes changed'\n"+text[end:]
    text=text.replace("for arm in ('checklist','cure_v01'):","for arm in ('checklist','cure_v01_c1'):")
    anchor="    require_gate(source/'study/cpu_gate.json',source)\n"
    extra="""    runner_gate=json.loads((source/'study/full_runner_cpu_gate.json').read_text())
    registration=json.loads((source/'study/runner_registration.json').read_text())
    assert runner_gate['passed'] is True and runner_gate['runner_tests_passed'] is True
    assert runner_gate['registration_sha256']==sha_file(source/'study/runner_registration.json')
    for name,digest in registration['source_hashes'].items():
        assert sha_file(source/name)==digest,name
"""
    text=text.replace(anchor,anchor+extra)
    text=text.replace('"""Frozen host-side GPU session. Stop on infrastructure failure; never retry a run."""',
        '"""Study 02 C1 session: pinned model bytes, full Runner CPU gate, fresh B/C1 pair."""')
    write_new(REPO/'cure/compat_v011/session.py',text.encode())
    diff=''.join(difflib.unified_diff(original.splitlines(keepends=True),text.splitlines(keepends=True),
        fromfile='frozen-gpu-mechanism-01/session.py',tofile='compat_v011/session.py'))
    write_new(STUDY/'session-adapter.diff',diff.encode())


def freeze():
    derive();derive_session()
    old=json.loads((REPO/'cure/gpu-study-01/protocol.json').read_text(encoding='utf-8'))
    gate=require_gate(REPO/'cure/results/cpu-r03/cpu_gate.json',REPO)
    row=old['tasks'][0]
    raw=(REPO/'cure/gpu-study-01/data/tasks.jsonl').read_bytes().splitlines(keepends=True)[0]
    write_new(STUDY/'data/tasks.jsonl',raw)
    write_new(STUDY/'data/snapshots'/f"{row['task_id']}.tgz",(REPO/'cure/gpu-study-01/data/snapshots'/f"{row['task_id']}.tgz").read_bytes())
    data=derive()
    candidates=dict(checklist=old['candidates']['checklist'],cure_v01_c1=dict(zip_sha256=data['new_zip_sha256'],bytes=data['zip_bytes'],members=data['members']))
    hashes=dict(gate['source_hashes'])
    for n in ('cure/gpu_mechanism/__init__.py','cure/gpu_mechanism/audit.py','cure/gpu_mechanism/worker_entry.py',
              'cure/compat_v011/__init__.py','cure/compat_v011/session.py','cure/compat_v011/test_runner.py'):
        hashes[n]=sha((REPO/n).read_bytes())
    for n in AGENT_FILES:
        rel='cure/candidates/cure_v01_c1/'+n;hashes[rel]=sha((REPO/rel).read_bytes())
    rel='cure/packages/cure_v01_c1/submission.zip';hashes[rel]=sha((REPO/rel).read_bytes())
    identity=json.loads((REPO/'cure/gpu-study-01/results/smoke/model_identity.json').read_text(encoding='utf-8'))
    plan=dict(experiment_id=EXPERIMENT,status_at_registration='not_executed',origin_commit='55e31b8768b0b71749fab83929e0fb4d8c0d6b9c',
        exploratory=True,prior_exposure='The same lumen scenario and prior B behavior were observed in study01. This is compatibility/mechanism exploration, not independent generalization evidence.',
        model=old['model'],model_alias=old['model_alias'],expected_model_files=identity['files'],
        expected_model_manifest_sha256=identity['manifest_sha256'],wheel_hashes=old['wheel_hashes'],
        wheelhouse_manifest_sha256=old['wheelhouse_manifest_sha256'],research_config=old['research_config'],generation=old['generation'],
        context=old['context'],runtime_source_hashes=hashes,candidates=candidates,tasks=[row],
        batches=dict(smoke=[dict(index=1,arm='checklist',**row),dict(index=2,arm='cure_v01_c1',**row)]),
        stop_rule='Stop globally on first compatibility/infrastructure/evidence gate failure. No temporary fix, retry, replacement, old-B reuse or splicing. A completed assertion failure remains a real task result, not an infrastructure failure.',
        mechanism_rule=old['mechanism_rule'],input_separation=old['input_separation'],
        outcomes=dict(A='Full Runner and real C1 request compatibility',B='Native tool-evidenced state-guided actions and confirmed counterevidence/revision opportunity, independent of self-report',
            C='No success-rate claim from one exposed synthetic pair'),lora=False,competition_submission=False)
    save(STUDY/'protocol.json',plan)
    save(STUDY/'runner-registration.json',dict(experiment_id=EXPERIMENT,source_hashes=hashes,
        required_legacy_tests=63,required_runner_tests=5,expected={'checklist':'HTTP request','cure_v01':'KeyError JSON before HTTP','cure_v01_c1':'HTTP request, JSON example byte-preserved','double_braces':'KeyError JSON before HTTP'}))
    print(json.dumps(dict(experiment_id=EXPERIMENT,protocol_sha256=sha((STUDY/'protocol.json').read_bytes()),candidate=data),indent=2))


def notebook(kind,runner_gate=None):
    plan=json.loads((STUDY/'protocol.json').read_text(encoding='utf-8'))
    registration=STUDY/'runner-registration.json'
    files={n:(REPO/n).read_bytes() for n in plan['runtime_source_hashes']}
    files.update({'study/protocol.json':(STUDY/'protocol.json').read_bytes(),
        'study/runner_registration.json':registration.read_bytes(),
        'study/cpu_gate.json':(REPO/'cure/results/cpu-r03/cpu_gate.json').read_bytes(),
        'cure/registrations/cpu-r03.json':(REPO/'cure/registrations/cpu-r03.json').read_bytes()})
    for p in (STUDY/'data').rglob('*'):
        if p.is_file():files['study/'+p.relative_to(STUDY).as_posix()]=p.read_bytes()
    if kind=='smoke':
        assert runner_gate,'Matching successful full Runner CPU gate required'
        gate=json.loads(Path(runner_gate).read_text(encoding='utf-8'))
        assert gate['passed'] is True and gate['registration_sha256']==sha(registration.read_bytes())
        files['study/full_runner_cpu_gate.json']=Path(runner_gate).read_bytes()
    payload=archive(files)
    setup=f'''import os,sys,json,hashlib,zipfile,io,subprocess,shutil,time
from pathlib import Path
from datetime import datetime,timezone
RUN_DIR=Path('/kaggle/working/cure_gpu_mechanism_02_c1')/{kind!r}/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
RUN_DIR.mkdir(parents=True,exist_ok=False)
SOURCE=RUN_DIR/'source'
payload=__import__('base64').b64decode({base64.b64encode(payload).decode()!r})
assert hashlib.sha256(payload).hexdigest()=={sha(payload)!r}
with zipfile.ZipFile(io.BytesIO(payload)) as z:
    assert z.testzip() is None
    assert all(not n.startswith('/') and '..' not in Path(n).parts for n in z.namelist())
    z.extractall(SOURCE)
sys.path.insert(0,str(SOURCE))
PLAN=json.loads((SOURCE/'study/protocol.json').read_text())
WHEELHOUSE_DIR=next(Path('/kaggle/input').rglob('swegemma-0.2.11-py3-none-any.whl')).parent
actual={{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in WHEELHOUSE_DIR.glob('*.whl') if 'cutlass' not in p.name.lower()}}
assert actual==PLAN['wheel_hashes'],'Wheel bytes changed'
(RUN_DIR/'wheel_hashes.json').write_text(json.dumps(actual,indent=2))
'''
    install=(REPO/'cure/notebooks/install_official.py').read_text(encoding='utf-8')
    if kind=='cpu':
        run='''from harness_v2.evidence import bundle
os.environ['CURE_COMPAT_CPU_DIR']=str(RUN_DIR/'runner-evidence')
try:
    for name,args in [('original63',['-m','cure.cpu_validation','cpu-r03',str(RUN_DIR/'validation')]),('runner',['-m','unittest','cure.compat_v011.test_runner','-v'])]:
        p=subprocess.run([sys.executable,*args],cwd=SOURCE,capture_output=True,text=True,timeout=1200)
        (RUN_DIR/(name+'.log')).write_text(p.stdout+p.stderr)
        print(name,p.stdout+p.stderr,flush=True)
        assert p.returncode==0,name
    cases={p.parent.name:json.loads(p.read_text()) for p in (RUN_DIR/'runner-evidence').glob('*/result.json')}
    assert set(cases)=={'checklist','cure_v01','cure_v01_c1','cure_v01-double-braces'}
    registration=SOURCE/'study/runner_registration.json'
    gate=dict(passed=True,runner_tests_passed=True,legacy_tests=63,runner_tests=5,mocked_HTTP=True,real_model_inference=False,
        registration_sha256=hashlib.sha256(registration.read_bytes()).hexdigest(),cases=cases)
    (RUN_DIR/'full_runner_cpu_gate.json').write_text(json.dumps(gate,indent=2))
finally:
    print('C1_CPU_EVIDENCE',bundle(RUN_DIR),flush=True)
'''
    else:
        setup+="os.environ.update(VLLM_WORKER_MULTIPROC_METHOD='spawn',VLLM_NO_USAGE_STATS='1',VLLM_ENGINE_READY_TIMEOUT_S='1200',VLLM_MEMORY_PROFILER_ESTIMATE_CUDAGRAPHS='1',NCCL_DEBUG='WARN',PYTORCH_CUDA_ALLOC_CONF='expandable_segments:True',LOCAL_API_KEY='EMPTY',OPENAI_API_KEY='EMPTY')\n"
        run='''from cure.compat_v011.session import run
from harness_v2.evidence import bundle
try:
    await run(SOURCE,RUN_DIR,'smoke')
finally:
    print('C1_GPU_EVIDENCE',bundle(RUN_DIR),flush=True)
'''
    cells=[]
    for code in (setup,install,run):
        compile(code,'<compat-notebook>','exec',flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
        cells.append(dict(cell_type='code',metadata={},source=code,outputs=[],execution_count=None,id=sha(code.encode())[:12]))
    nb=dict(cells=cells,metadata=dict(kernelspec=dict(display_name='Python 3',language='python',name='python3')),nbformat=4,nbformat_minor=5)
    raw=json.dumps(nb,indent=1).encode()
    base=REPO/'artifacts/cure-gpu-mechanism-02-c1'/kind/'kernel'
    write_new(base/'study.ipynb',raw)
    meta=json.loads((REPO/'artifacts/harness-v2/r12/gpu-kernel/kernel-metadata.json').read_text(encoding='utf-8'))
    meta.update(id='wudangdexiaodoashi/gemma4-cure-mechanism-02-c1-'+kind,title='Gemma4 CURE Mechanism 02 C1 '+kind,
        code_file='study.ipynb',enable_gpu=kind!='cpu',dataset_sources=['metric/gemma-4-developer-agent-wheelhouse'],
        model_sources=[] if kind=='cpu' else [plan['model']])
    write_new(base/'kernel-metadata.json',json.dumps(meta,indent=2).encode())
    save(STUDY/('notebook-'+kind+'.json'),dict(kernel_id=meta['id'],payload_sha256=sha(payload),notebook_sha256=sha(raw),
        protocol_sha256=sha((STUDY/'protocol.json').read_bytes()),status_at_registration='not_executed'))
    print(base)


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['freeze','cpu','smoke']);p.add_argument('--runner-gate')
    a=p.parse_args();freeze() if a.action=='freeze' else notebook(a.action,a.runner_gate)
