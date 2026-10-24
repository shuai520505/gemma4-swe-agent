"""Read-only evidence re-audit and reproducible binding. Never rebuild candidates."""
import base64
import hashlib
import inspect
import io
import json
from pathlib import Path
import subprocess
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MEER = HERE.parent
PR30 = ROOT/'u_re/v04/experiments/prospective_admission_01'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def put(name, value):
    path = HERE/name; path.parent.mkdir(parents=True, exist_ok=True)
    raw = value if isinstance(value, bytes) else (json.dumps(value, indent=2)+'\n').encode()
    if path.exists() and path.read_bytes() != raw:
        raise ValueError('Frozen output differs: '+name)
    if not path.exists():
        path.write_bytes(raw)


def evidence_audit():
    from meer.v01.audit import inspect_archive
    from u_re.v04.experiments.prospective_admission_01.audit import bind, native_counts
    lock = json.loads((MEER/'GPU_EXPERIMENT_LOCK.json').read_bytes())
    assert sha((ROOT/lock['task_source']).read_bytes()) == lock['task_source_sha256']
    manifest = json.loads((MEER/'CANDIDATE_MANIFEST.json').read_bytes())
    for arm, row in manifest['arms'].items():
        raw = (MEER/f'submission_{arm}.zip').read_bytes()
        assert sha(raw) == row['ZIP_sha256'] == lock['arms'][arm]['ZIP_sha256']
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            assert z.testzip() is None and set(z.namelist()) == set(row['members'])
            for n, h in row['members'].items():
                assert sha(z.read(n)) == h == sha((MEER/'candidates'/arm/n).read_bytes())
    # Re-read the actual private CPU archive, not just PASS fields.
    cpu = json.loads((MEER/'CPU_ACCEPTANCE_CPU03.json').read_bytes())
    raw = Path(cpu['raw_archive_path']).read_bytes()
    actual = inspect_archive('cpu03', raw, require_bypass=True)
    assert actual['archive_sha256'] == cpu['archive_sha256']
    # Revalidate historical source/version-bound native result artifacts.
    archive = Path(lock['tasks'][0]['source_archive']['private_path'])
    binding = bind(archive, 'screen01')
    assert binding['sha256'] == lock['tasks'][0]['source_archive']['sha256']
    tasks = []
    with zipfile.ZipFile(archive) as z:
        identity = json.loads(z.read('validation/TASK_IDENTITY_LOCK.json'))
        assert identity['checked_before_baselines'] and not identity['conflicts']
        ledger = json.loads(z.read('validation/TASK_ADMISSION_RESULTS.json'))
        for task in lock['tasks']:
            row = next(r for r in ledger['rows'] if r['instance_id'] == task['instance_id'])
            prefix = 'validation/'+row['raw_directory']+'/'
            native = z.read(prefix+'official_result.json'); junit = z.read(prefix+'phase2.junit.xml')
            assert sha(native) == task['TaskResult_sha256']
            assert sha(junit) == task['JUnit_sha256']
            assert native_counts(z, prefix) == task['native_baseline_counts']
            assert json.loads(native)['resolved'] is False
            assert z.read(prefix+'before.json') == z.read(prefix+'after.json')
            assert json.loads(z.read(prefix+'cleanup.json'))['complete']
            assert json.loads(z.read(prefix+'provenance.json'))['verified']
            assert task['formal_admission_status'] == 'BASELINE_ELIGIBLE'
            assert task['independent_environment_errors'] == 0 and not task['alias_conflicts']
            for key in ('repo','base_commit','issue_sha256','task_record_sha256','test_patch_sha256','input_files'):
                assert identity['all129'][task['instance_id']][key] == task[key]
            tasks.append(dict(instance_id=task['instance_id'], hashes_recomputed=True,
                              counts=task['native_baseline_counts'], cleanup=True,
                              TaskResult_sha256=sha(native), JUnit_sha256=sha(junit)))
    inherited = json.loads((PR30/'CPU_END_TO_END_ACCEPTANCE.json').read_bytes())
    assert sha((PR30/'payload.zip').read_bytes()) == inherited['payload_sha256']
    raw = Path(inherited['raw_archive_path']).read_bytes()
    assert sha(raw) == inherited['raw_archive_sha256']
    build = json.loads((PR30/inherited['attempt']/'BUILD.json').read_bytes())
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        assert z.testzip() is None
        for n, h in build['payload_members'].items():
            assert sha(z.read('source/'+n)) == h
    return dict(candidate_ZIPs_and_members_rehashed=True,
                CPU_Notebook=cpu['Notebook_id'], CPU_archive_sha256=cpu['archive_sha256'],
                CPU_payload_sha256=cpu['payload_sha256'], CPU_sources_verified=actual['source_members_verified'],
                admission_Notebook=binding['Notebook_id'], admission_archive_sha256=binding['sha256'],
                tasks=tasks, inherited_production_payload_sha256=inherited['payload_sha256'],
                inherited_production_sources_verified=len(build['payload_members']))


def build():
    from meer.v01.build import archive
    evidence = evidence_audit()
    protocol = json.loads((MEER/'GPU_EXPERIMENT_LOCK.json').read_bytes())
    inherited = json.loads((PR30/'ABBA_EXPERIMENT_LOCK.json').read_bytes())
    environment = (PR30/'ENVIRONMENT_LOCK.json').read_bytes()
    assert sha(environment) == protocol['tasks'][0]['environment_lock_sha256']
    runtime = dict(inherited, experiment_id=protocol['experiment'], arms=protocol['arms'],
                   tasks=protocol['tasks'], order=protocol['order'])
    put('RUNTIME_LOCK.json', runtime); put('ENVIRONMENT_LOCK.json', environment)
    # Hash accepted shared model/tool/source implementations, including the Guard.
    production_names = ['worker.py','session.py','__init__.py']
    pins = {f'meer/v01/gpu01/{n}': sha((HERE/n).read_bytes()) for n in production_names}
    reused = ['s1/config.py','s1/guard.py','harness_v2/context_budget.py',
              'harness_v2/official.py','s1/infrastructure_recovery/wire.py',
              'u_re/v01/experiments/action_priority_01/real_gemma_abba01/worker.py',
              'u_re/v01/experiments/action_priority_01/real_gemma_abba03/worker.py',
              'u_re/v01/experiments/action_priority_01/real_gemma_abba03/session.py',
              'u_re/v04/experiments/prospective_admission_01/session.py',
              'u_re/v02/experiments/env_recovery_admission_01/runtime.py',
              'u_re/v02/experiments/env_recovery_admission_01/junit_audit.py']
    pins.update({n: sha((ROOT/n).read_bytes()) for n in reused})
    manifest = dict(experiment_id=protocol['experiment'], source_base_commit=subprocess.check_output(
        ['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip(),
        preregistration_sha256=sha((MEER/'GPU_EXPERIMENT_LOCK.json').read_bytes()),
        arms=protocol['arms'], tasks=protocol['tasks'], budget=protocol['budget'],
        batches={'1': protocol['order'][:3], '2': protocol['order'][3:]},
        environment_lock_sha256=sha(environment), model=inherited['model'],
        production_source_pins=pins, evidence=evidence,
        production_entry='meer.v01.gpu01.session.run', GPU_authorized=False,
        authorization='External owner grant required; this preparation is not a grant',
        maximum_requested_window_seconds=10000, model_requests_per_readiness_check=0)
    put('EXECUTION_MANIFEST.json', manifest)
    with zipfile.ZipFile(PR30/'payload.zip') as z:
        assert z.testzip() is None
        files = {n: z.read(n) for n in z.namelist() if n != 'gpu_registration.json'}
    # Existing exact production closure is inherited; no hand-built abbreviated import list.
    for n in reused:
        assert n in files and sha(files[n]) == pins[n], n
    for n in production_names + ['RUNTIME_LOCK.json','ENVIRONMENT_LOCK.json','EXECUTION_MANIFEST.json']:
        files['meer/v01/gpu01/'+n] = (HERE/n).read_bytes()
    files['meer/__init__.py'] = b''
    for n in ('__init__.py','CANDIDATE_MANIFEST.json'):
        files['meer/v01/'+n] = (MEER/n).read_bytes()
    for arm in ('A','B','C'):
        raw = (MEER/f'submission_{arm}.zip').read_bytes()
        files[f'meer/v01/submission_{arm}.zip'] = raw
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            for n in z.namelist():
                files[f'meer/v01/candidates/{arm}/{n}'] = z.read(n)
    # Do not include a scripted model implementation in the MEER execution module.
    assert not any(n.startswith('meer/') and ('owned_transport' in n or 'cpu_acceptance' in n) for n in files)
    old = json.loads((PR30/'GPU03_PAYLOAD_MANIFEST.json').read_bytes())
    reg = dict(files={n:sha(b) for n,b in files.items()}, wheel_hashes=old['wheel_hashes'],
               production_entry=manifest['production_entry'], GPU_authorized=False)
    files['gpu_registration.json'] = (json.dumps(reg, indent=2)+'\n').encode()
    payload = archive(files); put('payload.zip', payload)
    put('PAYLOAD_BUILD.json', dict(payload_sha256=sha(payload), payload_bytes=len(payload),
        manifest_sha256=sha((HERE/'EXECUTION_MANIFEST.json').read_bytes()),
        production_entry=manifest['production_entry'], payload_members=reg['files'],
        GPU_SaveKernel_requests=0, authorization_record=None))
    from s1.prepare import INSTALL, IMAGE, MODEL_REF
    notebooks = []
    for batch in (1,2):
        setup = f'''import os,sys,json,hashlib,zipfile,io,subprocess,shutil,time
from pathlib import Path
SESSION_STARTED=time.monotonic()
# Must be supplied by the trusted dispatch operator after a separate owner grant.
AUTHORIZATION=None
assert AUTHORIZATION and AUTHORIZATION.get('GPU_authorized') is True, 'Gate F: GPU not authorized'
RUN_DIR=Path('/kaggle/working/meer-v01-gpu-batch{batch}');RUN_DIR.mkdir(parents=True,exist_ok=False)
SOURCE=RUN_DIR/'source'
payload=__import__('base64').b64decode({base64.b64encode(payload).decode()!r})
assert hashlib.sha256(payload).hexdigest()=={sha(payload)!r}
with zipfile.ZipFile(io.BytesIO(payload)) as z:
    assert z.testzip() is None and all(not n.startswith('/') and '..' not in Path(n).parts for n in z.namelist())
    z.extractall(SOURCE)
sys.path.insert(0,str(SOURCE))
REG=json.loads((SOURCE/'gpu_registration.json').read_bytes())
for n,h in REG['files'].items():assert hashlib.sha256((SOURCE/n).read_bytes()).hexdigest()==h,n
identity=dict(payload_sha256={sha(payload)!r},production_entry=REG['production_entry'])
(RUN_DIR/'PAYLOAD_IDENTITY.json').write_text(json.dumps(identity))
from meer.v01.gpu01.session import authorize
authorize(AUTHORIZATION,json.loads((SOURCE/'meer/v01/gpu01/EXECUTION_MANIFEST.json').read_bytes()),{batch},identity)
WHEELHOUSE_DIR=next(Path('/kaggle/input').rglob('swegemma-0.2.11-py3-none-any.whl')).parent
assert {{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in WHEELHOUSE_DIR.glob('*.whl') if 'cutlass' not in p.name.lower()}}==REG['wheel_hashes']
'''
        execute = INSTALL + f'''import asyncio
from harness_v2.evidence import bundle
from meer.v01.gpu01.session import run
try:
    asyncio.run(run(RUN_DIR/'execution',SESSION_STARTED,batch={batch},authorization=AUTHORIZATION,quota_at_dispatch=AUTHORIZATION['quota_at_dispatch_report_seconds']))
finally:
    print('MEER_GPU_EVIDENCE',bundle(RUN_DIR),flush=True)
'''
        for src in (setup,execute):
            compile(src, '<MEER-GPU-not-authorized>', 'exec')
        nb = dict(nbformat=4,nbformat_minor=5,metadata=dict(kernelspec=dict(name='python3',language='python',display_name='Python 3')),
                  cells=[dict(cell_type='code',source=s,id=sha(s.encode())[:12],metadata={},outputs=[],execution_count=None) for s in (setup,execute)])
        raw = (json.dumps(nb,indent=1)+'\n').encode()
        name = f'batch{batch:02d}/notebook'
        put(name+'/study.ipynb', raw)
        put(name+'/kernel-metadata.json', dict(id=f'wudangdexiaodoashi/meer-v01-gpu-batch{batch:02d}',
            title=f'MEER V01 GPU batch {batch:02d} NOT AUTHORIZED',code_file='study.ipynb',language='python',kernel_type='notebook',
            is_private=True,enable_gpu=True,enable_tpu=False,enable_internet=False,
            competition_sources=['gemma-4-developer-agent'],dataset_sources=['metric/gemma-4-developer-agent-wheelhouse'],
            model_sources=[MODEL_REF],kernel_sources=[],docker_image=IMAGE,docker_image_pinning_type='original'))
        notebooks.append(dict(batch=batch,Notebook_sha256=sha(raw),status='PREPARED_NOT_DISPATCHED',authorization_injected=False))
    put('NOTEBOOK_BUILD.json', dict(notebooks=notebooks, dispatch_function_included=False,
        note='Final external grant insertion changes outer Notebook SHA; freeze that authorized outer payload and once-only claim before any future save. Shared production ZIP is fixed.'))
    print(json.dumps(dict(payload_sha256=sha(payload), members=len(reg['files']), status='GPU_READY_NOT_AUTHORIZED')))


def readonly_preflight():
    from u_re.v01.experiments.action_priority_01.real_gemma_abba01 import launch as prior
    source = inspect.getsource(prior.preflight)
    source = source.replace("directory=HERE/'preflight'", "directory=HERE/'readonly01/preflight';directory.parent.mkdir(exist_ok=True)")
    source = source.replace("HERE.parent/'integrated_cpu_01/ABBA_EXPERIMENT_LOCK.json'", "HERE/'RUNTIME_LOCK.json'")
    source = source.replace('remaining>=20600', 'remaining>=41200')
    ns = dict(prior.__dict__, HERE=HERE, ROOT=ROOT, SLUG='wudangdexiaodoashi/meer-v01-gpu-batch01')
    exec(compile(source,'<Reused-bounded-readonly-preflight>','exec'),ns)
    return ns['preflight']()


if __name__ == '__main__':
    import sys
    if len(sys.argv)>1 and sys.argv[1]=='readonly':
        print(json.dumps(readonly_preflight()))
    else:
        build()
