"""Freeze new controlled tasks and produce CPU/GPU notebooks without launching them."""
import ast
import base64
import difflib
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile
from cure.build import archive, write_new
from cure.runner import require_gate
from cure.runtime_config import ResearchConfig
from .scenarios import CASES
from . import EXPERIMENT

ROOT=Path(__file__).resolve().parents[1]
STUDY=ROOT/'gpu-study-01'
REPO=ROOT.parent


def sha(data): return hashlib.sha256(data).hexdigest()
def save_json(path,data): write_new(path,(json.dumps(data,indent=2)+'\n').encode())


def freeze():
    gate_path=ROOT/'results/cpu-r03/cpu_gate.json'
    gate=require_gate(gate_path,REPO)
    tasks=[]; meta=[]; refs={}
    for case in CASES:
        with tempfile.TemporaryDirectory() as temp:
            d=Path(temp)
            for n,text in case['files'].items():
                p=d/n; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(text.encode())
            def git(*args): return subprocess.check_output(['git','-C',str(d),*args])
            git('-c','init.templateDir=','init','-q')
            git('config','core.autocrlf','false'); git('config','user.name','CURE Fixture')
            git('config','user.email','fixture@example.invalid')
            git('add','.')
            env=dict(os.environ,GIT_AUTHOR_DATE='2026-10-17T00:00:00Z',GIT_COMMITTER_DATE='2026-10-17T00:00:00Z')
            subprocess.run(['git','-C',str(d),'commit','-qm','Initial controlled repository'],env=env,check=True)
            commit=git('rev-parse','HEAD').decode().strip()
            tarbytes=io.BytesIO()
            with tarfile.open(fileobj=tarbytes,mode='w') as tar:
                for p in sorted(d.rglob('*')):
                    if not p.is_file(): continue
                    info=tarfile.TarInfo(p.relative_to(d).as_posix()); raw=p.read_bytes()
                    info.size=len(raw); info.mode=0o644; info.mtime=0
                    tar.addfile(info,io.BytesIO(raw))
            snapshot=gzip.compress(tarbytes.getvalue(),mtime=0)
            write_new(STUDY/'data/snapshots'/(case['id']+'.tgz'),snapshot)
            hidden=case['checks']
            patch=''.join(difflib.unified_diff([],hidden.splitlines(keepends=True),fromfile='/dev/null',tofile='b/tests/test_evaluation.py'))
            test_patch='diff --git a/tests/test_evaluation.py b/tests/test_evaluation.py\nnew file mode 100644\n'+patch
            task=dict(instance_id=case['id'],repo='cure_synthetic/'+case['id'],base_commit=commit,
                problem_statement=case['issue'],test_patch=test_patch,patch='')
            tasks.append(task)
            meta.append(dict(task_id=case['id'],category=case['category'],base_commit=commit,
                problem_sha256=sha(case['issue'].encode()),snapshot_sha256=sha(snapshot),
                test_patch_sha256=sha(test_patch.encode()),initial_files={n:sha(t.encode()) for n,t in case['files'].items()}))
            # Reference patch used only by CPU validation, not mounted into GPU Notebook.
            for n,text in case['reference'].items(): (d/n).write_bytes(text.encode())
            refs[case['id']]=git('diff','--binary').decode()
    write_new(STUDY/'data/tasks.jsonl',(''.join(json.dumps(t)+'\n' for t in tasks)).encode())
    save_json(STUDY/'evaluation-references.json',refs)
    save_json(STUDY/'cpu_gate.json',gate)
    save_json(STUDY/'cpu-r03-registration.json',json.loads((ROOT/'registrations/cpu-r03.json').read_text()))
    hashes=dict(gate['source_hashes'])
    for name in ('__init__.py','worker_entry.py','audit.py','session.py'):
        rel='cure/gpu_mechanism/'+name; hashes[rel]=sha((REPO/rel).read_bytes())
    candidates=json.loads((ROOT/'registrations/cpu-r03.json').read_text())['candidates']
    batches={}; index=1
    for batch,indices in [('smoke',[0]),('followup_a',[1]),('followup_b',[2,3])]:
        rows=[]
        for i in indices:
            for arm in (('checklist','cure_v01') if i%2==0 else ('cure_v01','checklist')):
                rows.append(dict(index=index,arm=arm,**meta[i])); index+=1
        batches[batch]=rows
    wheels=json.loads((REPO/'experiments/formal-paired-01/protocol.json').read_text())['wheel_hashes']
    plan=dict(experiment_id=EXPERIMENT,status_at_registration='not_executed',origin_commit='7aa7801a5629c3fef05242e23701c03cb922dd6a',
        model='google/gemma-4/Other/gemma-4-31b-it-qat-w4a16-ct/2',model_alias='gemma-4-31b-it-qat-w4a16-ct',
        model_sha_rule='Attest every mounted model file before first inference; all continuation batches must match smoke manifest. Version pinned to /2 before execution.',
        wheel_hashes=wheels,wheelhouse_manifest_sha256=sha(json.dumps(wheels,sort_keys=True).encode()),
        research_config=ResearchConfig().snapshot(),generation=dict(temperature=.2,top_p=.95,top_k=40),
        cpu_gate_sha256=sha(gate_path.read_bytes()),runtime_source_hashes=hashes,candidates=candidates,tasks=meta,batches=batches,
        context=dict(max_model_len=32768,safety_tokens=1024,compaction_interval=5,overlap_size=1,token_threshold=8192,event_retention_size=4),
        stop_rule='Global stop on first infrastructure/evidence gate failure. No retry, replacement, outcome-based selection or partial-pair splicing. Followups require complete smoke pair gate; followup_b also requires followup_a. A completed assertion failure is not infrastructure failure.',
        mechanism_rule='Independently inspect native tool sequences and visible claims: counterevidence must contradict an identifiable prior claim; subsequent relevant inspection/probe/change must have tool evidence. Lack of a prior wrong hypothesis means no contradiction opportunity, not success. Do not use decision_changed as proof.',
        input_separation='Snapshots contain initial code/public tests only. Hidden tests are Task.test_patch outside workspace and enter fresh Phase2 sandbox only. Reference solutions/scenario generators excluded from GPU source bundle. Subprocess is not an OS security boundary; audit model requests and tool paths for leakage.',
        analysis='Synthetic mechanism screening only; no Kaggle Resolution Rate or leaderboard estimate. Report all eight slots, unknown/not_run separately. No inferential significance claim from four scenarios.',
        competition_submission=False,lora=False)
    save_json(STUDY/'protocol.json',plan)
    return plan


def files(cpu=False,smoke_gate=None):
    plan=json.loads((STUDY/'protocol.json').read_text())
    data={n:(REPO/n).read_bytes() for n in plan['runtime_source_hashes']}
    data['cure/registrations/cpu-r03.json']=(ROOT/'registrations/cpu-r03.json').read_bytes()
    for p in (STUDY/'data').rglob('*'):
        if p.is_file(): data['study/'+p.relative_to(STUDY).as_posix()]=p.read_bytes()
    data['study/protocol.json']=(STUDY/'protocol.json').read_bytes()
    data['study/cpu_gate.json']=(ROOT/'results/cpu-r03/cpu_gate.json').read_bytes()
    if smoke_gate: data['study/smoke_gate.json']=Path(smoke_gate).read_bytes()
    if cpu:
        for p in (ROOT/'gpu_mechanism').glob('*.py'):
            data['cure/gpu_mechanism/'+p.name]=p.read_bytes()
        data['study/evaluation-references.json']=(STUDY/'evaluation-references.json').read_bytes()
    else:
        assert not any(n.endswith(('scenarios.py','evaluation-references.json','prepare.py','test_study.py','test_official_study.py')) for n in data)
    return data


def notebook(kind, smoke_gate=None):
    payload=archive(files(cpu=kind=='cpu',smoke_gate=smoke_gate))
    base=REPO/'artifacts/cure-gpu-mechanism-01'/kind
    setup=f'''import os,sys,json,hashlib,zipfile,io,subprocess,shutil,time
from pathlib import Path
from datetime import datetime,timezone
RUN_DIR=Path('/kaggle/working/cure_gpu_mechanism_01')/{kind!r}/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
RUN_DIR.mkdir(parents=True,exist_ok=False)
SOURCE=RUN_DIR/'source'
payload=__import__('base64').b64decode({base64.b64encode(payload).decode()!r})
assert hashlib.sha256(payload).hexdigest()=={sha(payload)!r}
with zipfile.ZipFile(io.BytesIO(payload)) as z:
    assert z.testzip() is None
    z.extractall(SOURCE)
sys.path.insert(0,str(SOURCE))
PLAN=json.loads((SOURCE/'study/protocol.json').read_text())
WHEELHOUSE_DIR=next(Path('/kaggle/input').rglob('swegemma-0.2.11-py3-none-any.whl')).parent
actual={{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in WHEELHOUSE_DIR.glob('*.whl') if 'cutlass' not in p.name.lower()}}
assert actual==PLAN['wheel_hashes'],'Wheelhouse bytes changed; stop before inference'
(RUN_DIR/'wheel_hashes.json').write_text(json.dumps(actual,indent=2))
'''
    install=(ROOT/'notebooks/install_official.py').read_text()
    if kind!='cpu':
        setup+="os.environ.update(VLLM_WORKER_MULTIPROC_METHOD='spawn',VLLM_NO_USAGE_STATS='1',VLLM_ENGINE_READY_TIMEOUT_S='1200',VLLM_MEMORY_PROFILER_ESTIMATE_CUDAGRAPHS='1',NCCL_DEBUG='WARN',PYTORCH_CUDA_ALLOC_CONF='expandable_segments:True',LOCAL_API_KEY='EMPTY',OPENAI_API_KEY='EMPTY')\n"
        run=f'''from cure.gpu_mechanism.session import run
try:
    await run(SOURCE,RUN_DIR,{kind!r})
finally:
    from harness_v2.evidence import bundle
    print('GPU_MECHANISM_EVIDENCE',bundle(RUN_DIR),flush=True)
'''
    else:
        run='''try:
    for label,args in [('original63',['-m','cure.cpu_validation','cpu-r03',str(RUN_DIR/'validation')]),('study',['-m','unittest','cure.gpu_mechanism.test_study','cure.gpu_mechanism.test_official_study','-v'])]:
        p=subprocess.run([sys.executable,*args],cwd=SOURCE,capture_output=True,text=True,timeout=1200)
        (RUN_DIR/(label+'.log')).write_text(p.stdout+p.stderr)
        print(label,p.stdout+p.stderr,flush=True)
        assert p.returncode==0,label
    (RUN_DIR/'study_cpu_gate.json').write_text(json.dumps({'passed':True,'gpu_inference':False}))
finally:
    from harness_v2.evidence import bundle
    print('CPU_STUDY_EVIDENCE',bundle(RUN_DIR),flush=True)
'''
    cells=[]
    for code in (setup,install,run):
        compile(code,'<study-notebook>','exec',flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
        cells.append(dict(cell_type='code',metadata={},source=code,outputs=[],execution_count=None,id=sha(code.encode())[:12]))
    nb=dict(cells=cells,metadata=dict(kernelspec=dict(display_name='Python 3',language='python',name='python3')),nbformat=4,nbformat_minor=5)
    raw=json.dumps(nb,indent=1).encode(); write_new(base/'kernel/study.ipynb',raw)
    meta=json.loads((REPO/'artifacts/harness-v2/r12/gpu-kernel/kernel-metadata.json').read_text())
    meta.update(id='wudangdexiaodoashi/gemma4-cure-mechanism-01-'+kind,title='Gemma4 CURE Mechanism 01 '+kind,
        code_file='study.ipynb',enable_gpu=kind!='cpu',dataset_sources=['metric/gemma-4-developer-agent-wheelhouse'],
        model_sources=[] if kind=='cpu' else ['google/gemma-4/Other/gemma-4-31b-it-qat-w4a16-ct/2'])
    write_new(base/'kernel/kernel-metadata.json',json.dumps(meta,indent=2).encode())
    save_json(STUDY/('notebook-'+kind+'.json'),dict(kind=kind,payload_sha256=sha(payload),notebook_sha256=sha(raw),
        protocol_sha256=sha((STUDY/'protocol.json').read_bytes()),notebook_id=meta['id'],status_at_registration='not_executed'))
    return str(base/'kernel')


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['freeze','cpu','smoke','followup_a','followup_b']);p.add_argument('--smoke-gate')
    a=p.parse_args()
    print(freeze() if a.action=='freeze' else notebook(a.action,a.smoke_gate))
