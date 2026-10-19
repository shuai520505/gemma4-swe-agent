"""New payloads assembled from accepted CPU03 bytes, not rewritten candidates."""
import ast
import base64
import json
from pathlib import Path
import zipfile
from experiments.prepare import write_new
from s1.prepare import IMAGE, INSTALL, MODEL_REF
from s1.util import archive, save, sha, sha_file

ROOT=Path(__file__).resolve().parents[3]; HERE=Path(__file__).resolve().parent
MODULE='s1.experiments.egv_mechanism_smoke_01'


def sources():
    accepted=ROOT/'s1/egv_v01'; reg=json.loads((accepted/'registration_cpu03.json').read_text())
    assert sha_file(accepted/'submission.zip')=='cefadd019ec64d9d06cbde72e0d0507796e8af9a370dd2358059e211845135e9'
    with zipfile.ZipFile(accepted/'results/cpu03/raw.zip') as z:
        assert z.testzip() is None
        files={n:z.read('source/'+n) for n in reg['source_hashes']}
    for n,h in reg['source_hashes'].items(): assert sha(files[n])==h,n
    for p in HERE.glob('*.py'): files[p.relative_to(ROOT).as_posix()]=p.read_bytes()
    files[(HERE/'selection.json').relative_to(ROOT).as_posix()]=(HERE/'selection.json').read_bytes()
    reg=dict(reg,experiment_id='s1-egv-mechanism-smoke-01',source_hashes={n:sha(b) for n,b in sorted(files.items())},GPU_permitted=False)
    return reg,files


def cpu(revision):
    reg,files=sources();save(HERE/('registration_'+revision+'.json'),reg)
    files['s1/registration.json']=(HERE/('registration_'+revision+'.json')).read_bytes()
    payload=archive(files)
    previous=json.loads((ROOT/'s1/egv_v01/notebooks/cpu03/study.ipynb').read_text())
    setup=previous['cells'][0]['source'];start=setup.index("payload=__import__('base64').b64decode(");end=setup.index('with zipfile.ZipFile',start)
    setup=setup[:start]+"payload=__import__('base64').b64decode("+repr(base64.b64encode(payload).decode())+")\nassert hashlib.sha256(payload).hexdigest()=="+repr(sha(payload))+"\n"+setup[end:]
    setup=setup.replace('s1_egv_v01','s1_egv_mechanism_smoke_01').replace("/'cpu03'/","/"+repr(revision)+"/")
    execute=f"p=subprocess.run([sys.executable,'-m',{MODULE+'.cpu'!r},str(RUN_DIR/'validation')],cwd=SOURCE,capture_output=True,text=True,timeout=3600)\n(RUN_DIR/'runner.stdout.log').write_text(p.stdout)\n(RUN_DIR/'runner.stderr.log').write_text(p.stderr)\nprint(p.stdout+p.stderr,flush=True)\nassert p.returncode==0,'Selected baseline or CPU compatibility blocked; no GPU'\n"
    code='from harness_v2.evidence import bundle\ntry:\n'+''.join('    '+line+'\n' for line in (INSTALL+'\n'+execute).splitlines())+"finally:print('EGV_MECHANISM_CPU_EVIDENCE',bundle(RUN_DIR),flush=True)\n"
    cells=[]
    for source in (setup,code):
        compile(source,'<CPU notebook>','exec',flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
        cells.append(dict(cell_type='code',metadata={},source=source,outputs=[],execution_count=None,id=sha(source.encode())[:12]))
    raw=(json.dumps(dict(cells=cells,metadata=previous['metadata'],nbformat=4,nbformat_minor=5),indent=1)+'\n').encode()
    folder=HERE/'notebooks'/revision;write_new(folder/'study.ipynb',raw)
    slug='gemma4-s1-egv-mech01-'+revision
    save(folder/'kernel-metadata.json',dict(id='wudangdexiaodoashi/'+slug,title=slug,code_file='study.ipynb',language='python',kernel_type='notebook',is_private=True,enable_gpu=False,enable_tpu=False,enable_internet=False,competition_sources=['gemma-4-developer-agent'],dataset_sources=['metric/gemma-4-developer-agent-wheelhouse'],model_sources=[],kernel_sources=[],docker_image=IMAGE,docker_image_pinning_type='original'))
    save(HERE/(revision+'_notebook.json'),dict(kernel='wudangdexiaodoashi/'+slug,notebook_sha256=sha(raw),payload_sha256=sha(payload),status_at_preparation='not_executed',GPU=False))
    print(folder)


def gpu(revision):
    reg,files=sources()
    assert reg==json.loads((HERE/('registration_'+revision+'.json')).read_text()),'CPU source drift'
    accepted=HERE/'_local'/(revision+'-extract')
    gate=json.loads((accepted/'validation/cpu_gate.json').read_text())
    assert gate['passed'] and gate['tests_run']==115 and gate['baseline']['eligible']
    assert gate['source_hashes']==reg['source_hashes']
    for n,h in reg['source_hashes'].items(): assert sha_file(accepted/'source'/n)==h,n
    draft=json.loads((ROOT/'s1/egv_v01/next_gpu_protocol_draft.json').read_text())
    candidates=json.loads((ROOT/'s1/candidates.json').read_text())
    control=dict(candidates['control'],directory='s1/candidates/control')
    egv=dict(json.loads((ROOT/'s1/egv_v01/candidate.json').read_text()),directory='s1/egv_v01/candidate')
    for arm,item,path in [('control',control,ROOT/'s1/packages/control/submission.zip'),('egv',egv,ROOT/'s1/egv_v01/submission.zip')]:
        assert sha_file(path)==item['zip_sha256'],arm
        for n,h in item['members'].items():assert sha_file(ROOT/item['directory']/n)==h,(arm,n)
    assert control['config']==egv['config']
    inputs=json.loads((accepted/'validation/selected_baseline/task_inputs.json').read_text())
    protocol=dict(experiment_id='s1-egv-mechanism-smoke-01',parent_commit='e355ce1b3dd6802706cdd69ae3b2da4736441406',
        infrastructure_version='s1-verifier-0.3.0',status_at_registration='not_executed',
        source_hashes=reg['source_hashes'],registration_sha256=sha_file(HERE/('registration_'+revision+'.json')),
        CPU_tests=115,CPU_gate_sha256=sha_file(accepted/'validation/cpu_gate.json'),CPU_raw_sha256=sha_file(HERE/'results'/revision/'raw.zip'),
        clean_baseline={n:sha_file(accepted/'validation/selected_baseline'/n) for n in ('official_result.json','phase2_execution.json','phase2.junit.xml','phase2_junit_capture.json','environment_admission.json','test_overlay_before_pytest.json','official_verifier_source.json','cleanup.json')},
        effective_environment=json.loads((accepted/'validation/selected_baseline/official_verifier_source.json').read_text())['versions'],
        model=MODEL_REF,model_files=draft['model_files'],wheel_hashes=reg['wheel_hashes'],task_wheel_hashes=reg['task_wheel_hashes'],
        selection=json.loads((HERE/'selection.json').read_text()),task_inputs=inputs,candidates=dict(egv=egv,control=control),
        prompt_diff_sha256=sha_file(ROOT/'s1/egv_v01/EGV_PROMPT_DIFF.md'),
        runs=[dict(index=i+1,instance_id='fastapi_15800',arm=arm) for i,arm in enumerate(('egv','control'))],
        condition='31B QATv2;4L4/TP4;context32768/safety1024;output16384/thinking4096;seed17;300s/60tools/command120s;six official tools;one Agent;sampling/include_thoughts omitted;only103-word EGV Prompt factor',
        isolation='Independent clean Agent sessions/workspaces and verifier sandboxes. Baseline/evaluator-only tests never enter Agent. No reference fix or previous Patch supplied.',
        clocks='10800s setup-origin window,900s finalization;startup requires1200+2*(1350+60);each next arm reserves all remaining1350+60 slots. Native Agent300/verifier300 unchanged.',
        startup='Eight model hashes,4L4;health/models/tokenize;one no-thinking16-output READY readiness probe (distinct from registered Agent generation);usage equality;oversize rejected;three idle samples.',
        verifier='Unmodified native Phase2/JUnit. Original XML copied before cleanup;strict XML/stdout/exit integrity. Native ordinary call failures continue other arm. Setup/collection/internal errors require clean-baseline and callchain attribution;unknown stops. No stdout word scanning.',
        cancellation='Every request_id has one actual terminal;CancelledError propagates;deadline and worker cleanup audited;unreceived usage null/partial. Require three zero-running/waiting server snapshots>=1s apart within60s. Not a request-specific server abort proof.',
        primary_endpoint='Complete unmodified official resolved;native TaskResult,test_exit_code,XML and stdout/stderr retained. unknown/not_run never confirmed failure.',
        mechanism='Anonymize tool actions and hide labels/final outcomes for initial validity,provenance,novelty,consequence review;seal first-pass audit before joining labels/costs/outcomes. Module import alone is not target reach;early edit/fewer tools not success.',
        stop='Hash/config drift,leakage,workspace contamination,unknown HTTP terminals,missing/conflicting JUnit,unattributed environment error,cleanup/nonidle/resources/evidence failures. Ordinary resolved=false,call failures,explained native deadline or fallback Patch do not stop. No retry/hotfix/task replacement/trajectory splicing.',
        decision='Resolved win with sound evidence or equal success/lower cost/preserved old behavior may justify new independent confirmation. Both fail but better probes only mechanism hint,no automatic expansion. Worse correctness/coverage or no useful action improvement+higher cost:No-Go/pause Prompt-only EGV.',
        interpretation='One paired public task cannot estimate population repair rate or gold/top5 probability;order/stochastic/task-specific effects remain.',
        authorization=dict(GPU_pairs=1,Agent_runs=2,other_tasks=False,LoRA=False,formal_submission=False,CURE=False))
    save(HERE/'protocol.json',protocol)
    files.update({'s1/registration.json':(HERE/('registration_'+revision+'.json')).read_bytes(),
        's1/cpu_gate.json':(accepted/'validation/cpu_gate.json').read_bytes(),
        's1/gpu_protocol.json':(HERE/'protocol.json').read_bytes()})
    payload=archive(files)
    cpu_nb=json.loads((HERE/'notebooks'/revision/'study.ipynb').read_text())
    setup=cpu_nb['cells'][0]['source'];start=setup.index("payload=__import__('base64').b64decode(");end=setup.index('with zipfile.ZipFile',start)
    setup=setup[:start]+"payload=__import__('base64').b64decode("+repr(base64.b64encode(payload).decode())+")\nassert hashlib.sha256(payload).hexdigest()=="+repr(sha(payload))+"\n"+setup[end:]
    setup=setup.replace('/'+repr(revision)+'/',"/'gpu'/")
    execute=f'from {MODULE}.session import run\nawait run(SOURCE,RUN_DIR,session_started=SESSION_STARTED)\n'
    code='from harness_v2.evidence import bundle\ntry:\n'+''.join('    '+line+'\n' for line in (INSTALL+'\n'+execute).splitlines())+"finally:print('EGV_MECHANISM_GPU_EVIDENCE',bundle(RUN_DIR),flush=True)\n"
    cells=[]
    for source in (setup,code):
        compile(source,'<GPU notebook>','exec',flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
        cells.append(dict(cell_type='code',metadata={},source=source,outputs=[],execution_count=None,id=sha(source.encode())[:12]))
    raw=(json.dumps(dict(cells=cells,metadata=cpu_nb['metadata'],nbformat=4,nbformat_minor=5),indent=1)+'\n').encode()
    folder=HERE/'notebooks/gpu';write_new(folder/'study.ipynb',raw)
    meta=json.loads((HERE/'notebooks'/revision/'kernel-metadata.json').read_text());slug='gemma4-s1-egv-mech01-gpu'
    meta.update(id='wudangdexiaodoashi/'+slug,title=slug,enable_gpu=True,machine_shape='NvidiaL4',model_sources=[MODEL_REF])
    save(folder/'kernel-metadata.json',meta)
    save(HERE/'gpu_notebook.json',dict(kernel=meta['id'],notebook_sha256=sha(raw),payload_sha256=sha(payload),protocol_sha256=sha_file(HERE/'protocol.json'),status_at_preparation='not_executed'))
    print(folder)


if __name__=='__main__':
    import sys
    cpu(sys.argv[1]) if sys.argv[1].startswith('cpu') else gpu(sys.argv[2])
