"""Frozen two-task paired GPU draft; raises before any side effect, never push."""
import ast
import base64
import hashlib
import io
import json
from pathlib import Path
import zipfile
from s1.util import archive,sha_file
from s2.egv_agenttool_t500_v01.config import Config
from experiments.prepare import write_new

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def emit(path,d):write_new(path,(json.dumps(d,indent=2)+'\n').encode())


def main():
    accepted=json.loads((HERE/'CPU_ACCEPTANCE.json').read_text());assert accepted['passed']
    env=json.loads((HERE/'results/env01/validation/environment_gate.json').read_text());assert env['passed']
    selected=json.loads((HERE/'TASK_SELECTION_PREREGISTRATION.json').read_text())
    old=ROOT/'s2/egv_agenttool_t500_v01'
    ancestor=json.loads((old/'GPU_PROTOCOL_T500_DRAFT.json').read_text())
    template=json.loads((ROOT/'s2/experiments/t500_agenttool_smoke_01/notebooks/gpu01/study.ipynb').read_text())
    setup=template['cells'][0]['source']
    line=next(s for s in setup.splitlines() if s.startswith("payload=__import__('base64').b64decode("))
    encoded=ast.literal_eval(line[len("payload=__import__('base64').b64decode("):-1])
    with zipfile.ZipFile(io.BytesIO(base64.b64decode(encoded))) as z:files={n:z.read(n) for n in z.namelist()}
    for n in ('s2/smoke_authorization.json','s2/smoke_cpu_gate.json','s2/smoke_protocol.json'):files.pop(n,None)
    for p in HERE.rglob('*'):
        rel=p.relative_to(HERE)
        if p.is_file() and not {'results','notebooks','registrations','__pycache__','_local'}.intersection(rel.parts) and (p.suffix=='.py' or 'candidate' in rel.parts or p.name in ('submission.zip','candidate.json','CPU_ACCEPTANCE.json')):
            files[p.relative_to(ROOT).as_posix()]=p.read_bytes()
    files['s2/early_cpu_acceptance.json']=(HERE/'CPU_ACCEPTANCE.json').read_bytes()
    candidates={}
    for arm,p in [('A',old),('B',HERE)]:
        c=json.loads((p/'candidate.json').read_text());c.update(directory=(p/'candidate').relative_to(ROOT).as_posix(),config=Config().snapshot())
        assert sha_file(p/'submission.zip')==c['zip_sha256'];candidates[arm]=c
    runs=[]
    for pair,row in enumerate(selected['selected'],1):
        for arm in (['A','B'] if pair==1 else ['B','A']):runs.append(dict(index=len(runs)+1,pair=pair,batch=1,instance_id=row['instance_id'],arm=arm))
    plan=dict(experiment_id='S2-T500-EARLYEGV-MECHANISM-01',status='DRAFT_NOT_AUTHORIZED',
        selected=selected['selected'],task_inputs=selected['task_inputs'],reserved_tasks=selected['reserved_eight_tasks'],
        exposed_exclusions=selected['excluded'],runs=runs,candidates=candidates,
        model=ancestor['model'],model_files=ancestor['model_files'],wheel_hashes=ancestor['wheel_hashes'],task_wheel_hashes=ancestor['task_wheel_hashes'],
        source_hashes={n:hashlib.sha256(b).hexdigest() for n,b in files.items()},
        CPU_acceptance_sha256=sha_file(HERE/'CPU_ACCEPTANCE.json'),environment_gate_sha256=sha_file(HERE/'results/env01/validation/environment_gate.json'),
        task_registration_sha256=sha_file(HERE/'TASK_SELECTION_PREREGISTRATION.json'),
        treatment='Only Main Prompt differs; joint early delegation/evidence discipline/closure workflow, not separable component effects.',
        shared_budget=Config().snapshot(),model_conditions='31BQATv2/4L4/TP4/context32768/safety1024/output16384/thinking4096/seed17; include_thoughts and sampling omitted',
        primary='Original official resolved per task; paired outcomes, unknown/not_run separate. Two tasks do not establish population repair-rate superiority.',
        mechanism='Real child assertion -> actionable counterevidence -> actual delivery -> Main production correction -> discriminating retest -> counterevidence eliminated; independent tool/path review required, no prose self-certification.',
        fairness='Fresh separate workspace/session/Verifier per arm; no first-arm outputs supplied to second. Same observer/native Phase2/context guard/budget. No reference repair access.',
        resource_window_seconds=10000,install_cap_seconds=300,startup_cap_seconds=1200,finalization_reserved_seconds=900,
        per_run_outer_seconds=1550,per_run_idle_gate_seconds=60,
        resource_model=dict(Agent_cap_sum_seconds=2000,full_worker_and_idle_slots_seconds=6440,
            expected_quota_to_wall_ratio=2,quota_reserve_required_seconds=20600,uncertainty='Machine accounting must be refreshed/verified; ratio measured once, not guaranteed'),
        stop='Hash/model/config drift; baseline/native Verifier fault; data leak; unknown HTTP terminal or conflicting/missing JUnit; child writes/concurrent delegation; cleanup/server idle unconfirmed; insufficient complete remaining slots/quota. Ordinary algorithm failures do not stop the paired second arm. Never hotfix/retry/substitute after outcomes.',
        GPU_authorized=False,GPU_executed=False,formal_submission=False,LoRA=False,
        pending='Explicit separate execution authorization plus fresh sufficient quota/machine admission and executable authorized version. Do not edit old frozen protocols.')
    emit(HERE/'GPU_MECHANISM_PROTOCOL_DRAFT.json',plan)
    files['s2/early_gpu_protocol.json']=(HERE/'GPU_MECHANISM_PROTOCOL_DRAFT.json').read_bytes()
    payload=archive(files)
    start=setup.index("payload=__import__('base64').b64decode(");end=setup.index('with zipfile.ZipFile',start)
    setup=setup[:start]+"payload=__import__('base64').b64decode("+repr(base64.b64encode(payload).decode())+")\nassert hashlib.sha256(payload).hexdigest()=="+repr(hashlib.sha256(payload).hexdigest())+"\n"+setup[end:]
    setup=setup[:setup.index('\nPLAN=')]
    setup=setup.replace("Path('/kaggle/working/s2_t500_agenttool_smoke_01')/'gpu01'/", "Path('/kaggle/working/s2_t500_early_v01')/'gpu-draft'/")
    setup="raise RuntimeError('DRAFT: no GPU authorization, insufficient recorded quota; prepare a new authorized version after all gates.')\n"+setup
    setup+="\nPLAN=json.loads((SOURCE/'s2/early_gpu_protocol.json').read_text())\nfor n,h in PLAN['source_hashes'].items():assert hashlib.sha256((SOURCE/n).read_bytes()).hexdigest()==h,n\n"
    execute=template['cells'][1]['source'];execute=execute[:execute.index('    from s2.experiments.t500_agenttool_smoke_01.session import run')]
    execute+="    from s2.egv_agenttool_t500_early_v01.gpu_session import run\n    await run(SOURCE,RUN_DIR,session_started=SESSION_STARTED,batch=1,authorization={'authorized':False})\nfinally:print('EARLY_GPU_DRAFT_EVIDENCE',bundle(RUN_DIR),flush=True)\n"
    cells=[]
    for s in (setup,execute):
        compile(s,'<guarded paired draft>','exec',flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
        cells.append(dict(cell_type='code',metadata={},source=s,outputs=[],execution_count=None,id=hashlib.sha256(s.encode()).hexdigest()[:12]))
    folder=HERE/'notebooks/gpu-draft';raw=(json.dumps(dict(cells=cells,metadata=template['metadata'],nbformat=4,nbformat_minor=5),indent=1)+'\n').encode()
    assert len(raw)<900000;write_new(folder/'study.ipynb',raw)
    meta=json.loads((ROOT/'s2/experiments/t500_agenttool_smoke_01/notebooks/gpu01/kernel-metadata.json').read_text())
    meta.update(id='wudangdexiaodoashi/gemma4-s2-early-egv-paired-draft',title='gemma4-s2-early-egv-paired-draft')
    emit(folder/'kernel-metadata.json',meta)
    emit(HERE/'GPU_DRAFT_FREEZE.json',dict(protocol_sha256=sha_file(HERE/'GPU_MECHANISM_PROTOCOL_DRAFT.json'),
        payload_sha256=hashlib.sha256(payload).hexdigest(),notebook_sha256=sha_file(folder/'study.ipynb'),
        metadata_sha256=sha_file(folder/'kernel-metadata.json'),GPU_dispatched=False,authorization=False))
    print('Prepared guarded4-run draft; no dispatch')


if __name__=='__main__':main()
