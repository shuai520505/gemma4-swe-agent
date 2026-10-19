"""Freeze a non-authorized eight-task draft; never push/launch GPU kernels."""
import ast
import base64
import hashlib
import json
from pathlib import Path
import zipfile
from experiments.prepare import write_new
from s1.config import Config
from s1.util import archive,sha_file

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
PARENT=ROOT/'s1/experiments/egv_mechanism_smoke_01'


def emit(path,data):
    write_new(path,(json.dumps(data,indent=2)+'\n').encode())


def main(environment_revision):
    accepted=json.loads((HERE/'CPU_FEASIBILITY.json').read_text());assert accepted['passed']
    envroot=HERE/'results'/environment_revision/'validation'
    env=json.loads((envroot/'environment_gate.json').read_text());assert env['passed'] and len(env['selected'])==8
    exact=HERE/'results/budget01/validation/exact_gate.json'
    assert json.loads(exact.read_text())['passed']
    original=json.loads((PARENT/'protocol.json').read_text())
    with zipfile.ZipFile(PARENT/'results/gpu/raw.zip') as z:
        files={n:z.read('source/'+n) for n in original['source_hashes']}
        for n in ('s1/registration.json','s1/gpu_protocol.json','s1/cpu_gate.json'):files[n]=z.read('source/'+n)
    for p in HERE.rglob('*.py'):
        if not {'_local','results','notebooks','__pycache__'}.intersection(p.relative_to(HERE).parts):
            files[p.relative_to(ROOT).as_posix()]=p.read_bytes()
    for p in (HERE/'candidate').rglob('*'):
        if p.is_file():files[p.relative_to(ROOT).as_posix()]=p.read_bytes()
    for n in ('candidate.json','submission.zip','CPU_FEASIBILITY.json','TASK_POOL_PREREGISTRATION.json'):
        files[(HERE/n).relative_to(ROOT).as_posix()]=(HERE/n).read_bytes()
    selected=env['selected'];tasks={};runs=[]
    for i,row in enumerate(selected,1):
        task=row['instance_id'];tasks.update(json.loads((envroot/task/'task_inputs.json').read_text()))
        order=('A','B') if i in (1,4,5,8) else ('B','A')
        for arm in order:runs.append(dict(index=len(runs)+1,pair=i,batch=1 if i<=4 else 2,instance_id=task,arm=arm))
    a=dict(json.loads((ROOT/'s1/egv_v01/candidate.json').read_text()),directory='s1/egv_v01/candidate')
    b=dict(json.loads((HERE/'candidate.json').read_text()),directory='s2/egv_agenttool_v01/candidate',config=Config().snapshot())
    assert sha_file(ROOT/'s1/egv_v01/submission.zip')==a['zip_sha256']
    assert sha_file(HERE/'submission.zip')==b['zip_sha256']==accepted['candidate_zip_sha256']
    plan=dict(experiment_id='S2-EGV-AGENTTOOL-MULTITASK-01',status='DRAFT_NOT_AUTHORIZED',
        parent_S1_commit='b80565a71395c4d1c012a9bfea3e561ddab255db',selected=selected,task_inputs=tasks,runs=runs,
        candidates=dict(A=a,B=b),source_hashes={n:hashlib.sha256(v).hexdigest() for n,v in files.items()},
        model=original['model'],model_files=original['model_files'],wheel_hashes=original['wheel_hashes'],task_wheel_hashes=original['task_wheel_hashes'],
        CPU_acceptance_sha256=sha_file(HERE/'CPU_FEASIBILITY.json'),environment_gate_sha256=sha_file(envroot/'environment_gate.json'),
        exact_budget_gate_sha256=sha_file(exact),exact_budget_raw_sha256=sha_file(HERE/'results/budget01/raw.zip'),
        pool_sha256=env['pool_sha256'],shared_budget=Config().snapshot(),
        conditions='31B QATv2,4L4/TP4,context32768,safety1024,output16384,thinking4096,seed17;sampling/include_thoughts omitted;300s/60 organizer-counted tools/120s command per task shared by both roles',
        treatment='Two complete architectures: single S1-EGV vs Main+EGV AgentTool. Prompt responsibility,schemas,history handling and inference all differ; not an isolated agent-count effect.',
        isolation='Independent clean per-arm sessions/workspaces/native Verifiers. No first-arm Patch/Trace/answers given to the other arm. Child shares only its own Main workspace/budget.',
        endpoint='Unmodified official resolved; preserve original TaskResult,Phase2 exit/stdout/stderr/JUnit. unknown/not_run never confirmed failure. Full success rates only with all8 auditable pairs.',
        mechanism='Review actual tool validity/provenance/novelty/consequence and role-based discovery->delivery->Main production edit->real successful retest pointers. Reports alone never establish execution. Zero denominators=null.',
        budget_semantics='AgentTool/status/submit are not charged; inner bound read/edit/write/run share one cap. Exhaustion denies charged operations but may allow continued model calls/free submit. Native300s deadline encloses child.',
        stop='Hash/model/config drift;leakage;unexplained HTTP lifecycle;missing/conflicting JUnit;unattributed environment fault;cleanup/nonidle/global resource failure;observed child workspace write or ambiguous concurrent delegation. Ordinary assertion failure,attributed Agent regression or explained deadline/fallback do not stop.',
        batching='Two independent batches4 complete pairs each,2AB+2BA each. Batch2 requires a verified local receipt of batch1 complete evidence and same protocol/model. Do not mount first-arm answers in Agent workspaces.',
        resource_window_seconds=14400,finalization_reserved_seconds=900,per_run_outer_seconds=1350,per_run_idle_gate_seconds=60,
        quota_status='NOT_VERIFIED',GPU_authorized=False,GPU_executed=False,formal_submission=False,LoRA=False,
        pending_Go='Actual quota/window and explicit authorization;authorized final protocol/Notebook hashes;real Gemma startup/child request and reclamation gates. CPU mock success does not satisfy GPU inference gates.')
    emit(HERE/'MULTITASK_GPU_PROTOCOL_DRAFT.json',plan)
    files['s2/gpu_protocol.json']=(HERE/'MULTITASK_GPU_PROTOCOL_DRAFT.json').read_bytes()
    payload=archive(files)
    source_cpu=json.loads((HERE/'notebooks'/accepted['revision']/'study.ipynb').read_text())
    bindings={}
    for batch in (1,2):
        setup=source_cpu['cells'][0]['source'];start=setup.index("payload=__import__('base64').b64decode(");end=setup.index('with zipfile.ZipFile',start)
        setup=setup[:start]+"payload=__import__('base64').b64decode("+repr(base64.b64encode(payload).decode())+")\nassert hashlib.sha256(payload).hexdigest()=="+repr(hashlib.sha256(payload).hexdigest())+"\n"+setup[end:]
        # Do not use stale CPU-registration source verification after replacing
        # the payload: bind this full draft payload by SHA and protocol sources.
        setup=setup[:setup.index('\nS2REG=')]
        setup+="\nS2PLAN=json.loads((SOURCE/'s2/gpu_protocol.json').read_text())\nfor n,h in S2PLAN['source_hashes'].items():\n    assert hashlib.sha256((SOURCE/n).read_bytes()).hexdigest()==h,n\n"
        setup=setup.replace('/'+repr(accepted['revision'])+'/',"/'gpu-batch"+str(batch)+"-draft'/")
        setup="raise RuntimeError('DRAFT: GPU execution is not authorized; regenerate and register an authorized build after quota and user approval.')\n"+setup
        install=source_cpu['cells'][1]['source'];install=install[:install.index('    p=subprocess.run(')]
        execute="    from s2.egv_agenttool_v01.session import run\n    await run(SOURCE,RUN_DIR,session_started=SESSION_STARTED,batch="+str(batch)+",authorization={'authorized':False})\nfinally:print('S2_GPU_DRAFT_EVIDENCE',bundle(RUN_DIR),flush=True)\n"
        cells=[]
        for s in (setup,install+execute):
            compile(s,'<GPU draft>', 'exec',flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
            cells.append(dict(cell_type='code',metadata={},source=s,outputs=[],execution_count=None,id=hashlib.sha256(s.encode()).hexdigest()[:12]))
        raw=(json.dumps(dict(cells=cells,metadata=source_cpu['metadata'],nbformat=4,nbformat_minor=5),indent=1)+'\n').encode()
        folder=HERE/'notebooks'/('gpu-batch'+str(batch)+'-draft');write_new(folder/'study.ipynb',raw)
        metadata=json.loads((PARENT/'notebooks/gpu/kernel-metadata.json').read_text());metadata.update(id='wudangdexiaodoashi/gemma4-s2-egv-agenttool-batch'+str(batch)+'-draft',title='S2 AgentTool batch'+str(batch)+' DRAFT')
        emit(folder/'kernel-metadata.json',metadata)
        bindings[str(batch)]=dict(notebook_sha256=hashlib.sha256(raw).hexdigest(),metadata_sha256=sha_file(folder/'kernel-metadata.json'),dispatched=False)
    emit(HERE/'GPU_DRAFT_FREEZE.json',dict(status='DRAFT_NEVER_DISPATCHED',protocol_sha256=sha_file(HERE/'MULTITASK_GPU_PROTOCOL_DRAFT.json'),payload_sha256=hashlib.sha256(payload).hexdigest(),notebooks=bindings))
    emit(HERE/'FROZEN_TASKS.json',dict(selected=selected,runs=runs,all_frozen_before_first_GPU=True,GPU_runs=0))
    print('Prepared two guarded GPU Notebook drafts; not dispatched.')


if __name__=='__main__':
    import sys
    main(sys.argv[1])
