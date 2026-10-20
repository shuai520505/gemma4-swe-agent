"""Build CPU gate first; freeze a one-run GPU Notebook only after its evidence."""
import ast
import base64
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile
from s1.util import archive, sha_file
from experiments.prepare import write_new

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OLD = ROOT/'s2/egv_agenttool_t500_v01'


def emit(path, value):
    write_new(path, (json.dumps(value, indent=2)+'\n').encode())


def base_files():
    nb = json.loads((OLD/'notebooks/gpu-batch1-draft/study.ipynb').read_text())
    setup = nb['cells'][0]['source']
    line = next(x for x in setup.splitlines() if x.startswith("payload=__import__('base64').b64decode("))
    encoded = ast.literal_eval(line[len("payload=__import__('base64').b64decode("):-1])
    with zipfile.ZipFile(io.BytesIO(base64.b64decode(encoded))) as z:
        assert z.testzip() is None
        files = {n:z.read(n) for n in z.namelist()}
    parent = json.loads((OLD/'GPU_PROTOCOL_T500_DRAFT.json').read_text())
    for name, digest in parent['source_hashes'].items():
        assert hashlib.sha256(files[name]).hexdigest() == digest, name
        if name.startswith('s2/egv_agenttool_t500_v01/'):
            assert sha_file(ROOT/name) == digest, name
    files.pop('s2/gpu_protocol.json')
    for p in HERE.glob('*.py'):
        files[p.relative_to(ROOT).as_posix()] = p.read_bytes()
    return nb, files, parent


def build(stage):
    assert stage in ('cpu02', 'gpu01')
    nb, files, parent = base_files()
    if stage == 'cpu02':
        reserved = {r['instance_id'] for r in parent['selected']}
        pool = json.loads((ROOT/'s2/egv_agenttool_v01/TASK_POOL_PREREGISTRATION.json').read_text())
        screened = json.loads((ROOT/'s2/egv_agenttool_v01/results/env01/validation/environment_gate.json').read_text())
        by_id = {r['instance_id']:r for r in screened['records']}
        # First pre-ranked eligible task outside eight reserved pairs, metadata only.
        chosen = next(r for r in pool['pool'] if r['instance_id'] not in reserved and by_id[r['instance_id']]['eligible'])
        assert chosen['instance_id'] == 'rich_3471'
        identities = json.loads((ROOT/f"s2/egv_agenttool_v01/results/env01/validation/{chosen['instance_id']}/task_inputs.json").read_text())
        plan = {k:parent[k] for k in ('model','model_files','wheel_hashes','task_wheel_hashes','shared_budget')}
        plan.update(experiment_id='S2-T500-AGENTTOOL-SMOKE-01', status='AUTHORIZED_ONE_SMOKE_CPU_GATE_PENDING',
            authorization='User: 閭ｄ綘瑕佷笉鍏堟悶涓狦PUnotebook璇曡瘯; one independent smoke only, not 16 runs or formal submission.',
            development_base='25f6fed8b681398b23ffec9c8a162b63f203fa00',
            selection_rule='First previously CPU-eligible task in immutable24-pool order excluding all8 reserved paired tasks; no reference repair read; no replacement after freeze.',
            reserved_tasks=sorted(reserved), selected=[chosen], task_inputs=identities,
            candidates={'B':parent['candidates']['B']}, runs=[dict(index=1,pair=None,batch=1,instance_id=chosen['instance_id'],arm='B')],
            source_hashes={n:hashlib.sha256(b).hexdigest() for n,b in files.items()},
            resource_window_seconds=2700, install_cap_seconds=300, startup_cap_seconds=600,
            pre_server_environment_cap_seconds=300, finalization_reserved_seconds=180,
            per_run_outer_seconds=1550, per_run_idle_gate_seconds=60,
            quota_observation='API2026-10-20: total21600s,used18574.56.0s,reserved0; malformed duration preserved separately. Approx3025s; request2700s. Backend must admit 4L4 reservation, no quota guarantees.',
            stop='CPU/hash/input/model/config drift; baseline environment/cleanup failure; device mismatch; insufficient complete-slot admission; unexplained HTTP/JUnit; child workspace writes/concurrent delegation; service idle/cleanup unconfirmed. Ordinary attributable algorithm failures are recorded. Never retry after model result; no task substitution.',
            interpretation='Single-arm exploratory smoke; no A/B comparison or overall repair-rate claim. No forced child invocation or artificial faulty patch. No delegation/counterevidence means mechanism not established.',
            GPU_executed=False, formal_submission=False, LoRA=False)
        emit(HERE/'protocol_cpu02.json', plan)
    else:
        plan = json.loads((HERE/'protocol_cpu02.json').read_text())
        gate_file=HERE/'results/cpu02/validation/cpu_gate.json'
        gate=json.loads(gate_file.read_text()); assert gate['passed'] and not gate['real_Gemma']
        emit(HERE/'GPU_AUTHORIZATION.json',dict(experiment_id=plan['experiment_id'],authorized=True,max_runs=1,
            protocol_sha256=sha_file(HERE/'protocol_cpu02.json'),cpu_gate_sha256=sha_file(gate_file),
            cpu_raw_sha256=sha_file(HERE/'results/cpu02/raw.zip'),automatic_retries=0))
        files['s2/smoke_cpu_gate.json']=gate_file.read_bytes()
        files['s2/smoke_authorization.json']=(HERE/'GPU_AUTHORIZATION.json').read_bytes()
    # Frozen payload bytes are authoritative; old study and all candidates untouched.
    for n,h in plan['source_hashes'].items(): assert hashlib.sha256(files[n]).hexdigest()==h,n
    files['s2/smoke_protocol.json']=(HERE/'protocol_cpu02.json').read_bytes()
    payload=archive(files)
    setup=nb['cells'][0]['source'];setup=setup[setup.index('import os,sys'):]
    start=setup.index("payload=__import__('base64').b64decode(");end=setup.index('with zipfile.ZipFile',start)
    setup=setup[:start]+"payload=__import__('base64').b64decode("+repr(base64.b64encode(payload).decode())+")\nassert hashlib.sha256(payload).hexdigest()=="+repr(hashlib.sha256(payload).hexdigest())+"\n"+setup[end:]
    setup=setup[:setup.index('\nS2PLAN=')]
    setup=setup.replace("Path('/kaggle/working/s2_egv_agenttool_t500_v01')/'gpu-batch1-draft'/", "Path('/kaggle/working/s2_t500_agenttool_smoke_01')/"+repr(stage)+"/")
    setup+="\nPLAN=json.loads((SOURCE/'s2/smoke_protocol.json').read_text())\nfor n,h in PLAN['source_hashes'].items():assert hashlib.sha256((SOURCE/n).read_bytes()).hexdigest()==h,n\nprint('SOURCE_AND_WHEELS_VERIFIED',flush=True)\n"
    install=nb['cells'][1]['source'];install=install[:install.index('    from s2.egv_agenttool_t500_v01.session import run')]
    if stage=='gpu01':
        install=install.replace('timeout=1800','timeout=300')
        execute="    from s2.experiments.t500_agenttool_smoke_01.session import run\n    await run(SOURCE,RUN_DIR,session_started=SESSION_STARTED,batch=1,authorization=json.loads((SOURCE/'s2/smoke_authorization.json').read_text()))\n"
    else:
        execute="    with (RUN_DIR/'cpu.log').open('x') as log:\n        result=subprocess.run([sys.executable,'-m','s2.experiments.t500_agenttool_smoke_01.cpu',str(RUN_DIR/'validation')],stdout=log,stderr=subprocess.STDOUT,timeout=1200)\n    assert result.returncode==0,(RUN_DIR/'cpu.log').read_text()[-8000:]\n"
    install+=execute+"finally:print('S2_T500_SMOKE_EVIDENCE',bundle(RUN_DIR),flush=True)\n"
    cells=[]
    for s in (setup,install):
        compile(s,'<smoke notebook>','exec',flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
        cells.append(dict(cell_type='code',metadata={},source=s,outputs=[],execution_count=None,id=hashlib.sha256(s.encode()).hexdigest()[:12]))
    raw=(json.dumps(dict(cells=cells,metadata=nb['metadata'],nbformat=4,nbformat_minor=5),indent=1)+'\n').encode()
    assert len(raw)<900000
    folder=HERE/'notebooks'/stage;write_new(folder/'study.ipynb',raw)
    meta=json.loads((OLD/'notebooks/gpu-batch1-draft/kernel-metadata.json').read_text())
    slug='gemma4-s2-t500-smoke-'+stage
    meta.update(id='wudangdexiaodoashi/'+slug,title=slug,enable_gpu=stage=='gpu01')
    if stage=='cpu02':meta.pop('machine_shape',None)
    emit(folder/'kernel-metadata.json',meta)
    emit(HERE/(stage+'_freeze.json'),dict(protocol_sha256=sha_file(HERE/'protocol_cpu02.json'),
        payload_sha256=hashlib.sha256(payload).hexdigest(),notebook_sha256=sha_file(folder/'study.ipynb'),
        metadata_sha256=sha_file(folder/'kernel-metadata.json'),kernel=meta['id'],formal_submission=False))
    print(folder)


if __name__=='__main__':build(sys.argv[1])
