"""Derive an authorized execution build without rewriting the frozen GPU draft."""
import ast
import base64
import copy
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import subprocess
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EARLY = ROOT / 's2/egv_agenttool_t500_early_v01'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def emit(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as handle:
        handle.write(json.dumps(obj, indent=2) + '\n')


def main():
    from s2.egv_agenttool_t500_early_v01.audit import inspect
    from s2.egv_agenttool_t500_early_v01.gpu_session import require_authorization
    checked = inspect()
    emit(HERE / 'FROZEN_CPU_AND_CANDIDATE_RECHECK.json', checked)
    admission = load(HERE / 'GPU_RESOURCE_ADMISSION.json')
    assert admission['quota_passed'] and admission['no_observed_recent_saved_session_conflict']
    assert not admission['duplicate_saved_execution']
    original = load(EARLY / 'GPU_MECHANISM_PROTOCOL_DRAFT.json')
    freeze = load(EARLY / 'GPU_DRAFT_FREEZE.json')
    draft = load(EARLY / 'notebooks/gpu-draft/study.ipynb')
    assert sha((EARLY / 'GPU_MECHANISM_PROTOCOL_DRAFT.json').read_bytes()) == freeze['protocol_sha256']
    assert sha((EARLY / 'notebooks/gpu-draft/study.ipynb').read_bytes()) == freeze['notebook_sha256']
    setup = draft['cells'][0]['source']
    first, setup = setup.split('\n', 1)
    assert first.startswith('raise RuntimeError(')
    tree = ast.parse(setup)
    node = next(n for n in ast.walk(tree) if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == 'payload' for t in n.targets))
    payload = base64.b64decode(ast.literal_eval(node.value.args[0]))
    assert sha(payload) == freeze['payload_sha256']
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        assert z.testzip() is None
        files = {name: z.read(name) for name in z.namelist()}
    plan = copy.deepcopy(original)
    plan['status'] = 'AUTHORIZED_FROZEN'
    plan['GPU_authorized'] = True
    plan['pending'] = 'Authorized exactly four runs; one saved GPU Notebook; runtime admission before inference. No retry, substitution, new leaderboard submission or LoRA.'
    gate_name = 's2/experiments/earlyegv_mechanism_01/runtime_gate.py'
    files['s2/experiments/earlyegv_mechanism_01/__init__.py'] = (HERE / '__init__.py').read_bytes()
    files[gate_name] = (HERE / 'runtime_gate.py').read_bytes()
    for name in ('s2/experiments/earlyegv_mechanism_01/__init__.py', gate_name):
        plan['source_hashes'][name] = sha(files[name])
    for arm in ('A', 'B'):
        c = plan['candidates'][arm]
        parent = Path(c['directory']).parent
        raw = (ROOT / parent / 'submission.zip').read_bytes()
        assert sha(raw) == c['zip_sha256']
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            assert z.testzip() is None
            assert set(z.namelist()) == set(c['members'])
            for name, expected in c['members'].items():
                assert sha(z.read(name)) == expected
                assert z.read(name) == files[c['directory'] + '/' + name]
        target = HERE / 'frozen_candidates' / (arm + '.zip')
        target.parent.mkdir(exist_ok=True)
        with target.open('xb') as handle:
            handle.write(raw)
        # Source payload contains exact original candidate, no research files in Agent ZIP.
        files[(parent / 'submission.zip').as_posix()] = raw
    immutable = set(original) - {'status', 'GPU_authorized', 'pending', 'source_hashes'}
    assert all(plan[k] == original[k] for k in immutable)
    for name, expected in original['source_hashes'].items():
        assert sha(files[name]) == expected
    plan_raw = (json.dumps(plan, indent=2) + '\n').encode()
    emit(HERE / 'AUTHORIZED_PROTOCOL.json', plan)
    authorization = dict(
        authorized=True, max_runs=4, experiment_id=original['experiment_id'],
        granted_by='Human user in current Codex message; explicit conditional four-run authorization.',
        granted_recorded_at_utc=datetime.now(timezone.utc).isoformat(),
        source_commit='fce198a25502a8cd05f70d2f8704c21c25be84b2', candidate_freeze_commit='272c28401a9932b0d900e40f67ff088fc7eb1c43',
        protocol_sha256=sha(plan_raw), original_draft_protocol_sha256=freeze['protocol_sha256'],
        cpu_gate_sha256=original['CPU_acceptance_sha256'],
        requested_machine_shape='NvidiaL4', requested_notebook_window_seconds=10000,
        fresh_quota_and_machine_admission_verified=False, prelaunch_resource_admission=admission,
        model=original['model'], candidate_hashes={a: original['candidates'][a]['zip_sha256'] for a in ('A', 'B')},
        runs=original['runs'], forbidden=['additional saves/retries', 'extra Agent runs', 'changed candidates', 'changed tasks/order', 'leaderboard submission', 'LoRA'],
    )
    emit(HERE / 'GPU_AUTHORIZATION.json', authorization)
    files['s2/early_gpu_protocol.json'] = plan_raw
    files['s2/early_execution_authorization.json'] = (json.dumps(authorization, indent=2) + '\n').encode()
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for name, raw in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, raw)
    payload = out.getvalue()
    with (HERE / 'payload.zip').open('xb') as handle:
        handle.write(payload)
    start = setup.index("payload=__import__('base64').b64decode(")
    end = setup.index('with zipfile.ZipFile', start)
    setup = setup[:start] + "payload=__import__('base64').b64decode(" + repr(base64.b64encode(payload).decode()) + ")\nassert hashlib.sha256(payload).hexdigest()==" + repr(sha(payload)) + '\n' + setup[end:]
    setup = setup.replace("Path('/kaggle/working/s2_t500_early_v01')/'gpu-draft'/", "Path('/kaggle/working/s2_earlyegv_mechanism_01')/'gpu01'/")
    setup = setup.replace('SESSION_STARTED=time.monotonic()', '''# Include container startup time rather than resetting the window after installation.
import psutil
CONTAINER_STARTED_EPOCH=psutil.Process(1).create_time()
SESSION_STARTED=time.monotonic()-max(0,time.time()-CONTAINER_STARTED_EPOCH)''')
    setup += "\n(RUN_DIR/'execution_clock.json').write_text(json.dumps(dict(container_started_epoch=CONTAINER_STARTED_EPOCH,first_cell_epoch=time.time(),session_started_monotonic=SESSION_STARTED,elapsed=time.monotonic()-SESSION_STARTED),indent=2))\n"
    # Preserve setup exceptions even when Notebook execution does not enter cell2.
    split = setup.index("payload=__import__('base64').b64decode(")
    setup = setup[:split] + 'try:\n' + '\n'.join('    ' + line for line in setup[split:].splitlines()) + '''
except BaseException as exc:
    import traceback
    (RUN_DIR/'setup_exception.json').write_text(json.dumps(dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc()),indent=2))
    try:
        from harness_v2.evidence import bundle
        print('EARLY_GPU_SETUP_STOP_EVIDENCE',bundle(RUN_DIR),flush=True)
    except Exception as archive_error:print('SETUP_ARCHIVE_ERROR',repr(archive_error),flush=True)
    raise
'''
    execute = draft['cells'][1]['source']
    execute = execute.replace("    from s2.egv_agenttool_t500_early_v01.gpu_session import run", "    from s2.experiments.earlyegv_mechanism_01.runtime_gate import admit\n    authorization=json.loads((SOURCE/'s2/early_execution_authorization.json').read_text())\n    authorization=admit(SOURCE,RUN_DIR,SESSION_STARTED,authorization)\n    from s2.egv_agenttool_t500_early_v01.gpu_session import run")
    execute = execute.replace("authorization={'authorized':False}", 'authorization=authorization')
    execute = execute.replace("finally:print('EARLY_GPU_DRAFT_EVIDENCE'", "except BaseException as exc:\n    import traceback\n    (RUN_DIR/'execution_exception.json').write_text(json.dumps(dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc()),indent=2))\n    raise\nfinally:print('EARLY_GPU_AUTHORIZED_EVIDENCE'")
    notebook = copy.deepcopy(draft)
    for cell, source in zip(notebook['cells'], (setup, execute)):
        compile(source, '<authorized-notebook>', 'exec', flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
        cell.update(source=source, id=sha(source.encode())[:12], outputs=[], execution_count=None)
    folder = HERE / 'notebooks/gpu01'
    emit(folder / 'study.ipynb', notebook)
    metadata = load(EARLY / 'notebooks/gpu-draft/kernel-metadata.json')
    metadata.update(id='wudangdexiaodoashi/gemma4-s2-earlyegv-mechanism-01', title='gemma4-s2-earlyegv-mechanism-01')
    emit(folder / 'kernel-metadata.json', metadata)
    assert len((folder / 'study.ipynb').read_bytes()) < 900000
    try:
        require_authorization(plan, authorization, 1)
    except AssertionError:
        blocked_without_machine = True
    else:
        raise AssertionError('Unverified machine must not enter frozen coordinator')
    require_authorization(plan, dict(authorization, fresh_quota_and_machine_admission_verified=True), 1)
    emit(HERE / 'EXECUTION_BUILD_MANIFEST.json', dict(
        experiment_id=original['experiment_id'], created_at_utc=datetime.now(timezone.utc).isoformat(),
        baseline_commit=authorization['source_commit'], original_draft_freeze=freeze,
        authorized_protocol_sha256=sha(plan_raw), payload_sha256=sha(payload),
        notebook_sha256=sha((folder / 'study.ipynb').read_bytes()),
        notebook_API_text_sha256=sha(json.dumps(notebook).encode()), metadata_sha256=sha((folder / 'kernel-metadata.json').read_bytes()),
        authorization_sha256=sha((HERE / 'GPU_AUTHORIZATION.json').read_bytes()),
        unchanged_original_source_bindings=len(original['source_hashes']),
        original_draft_unchanged=True, frozen_candidate_differences=['prompts/main.md'],
        added_execution_only_sources={gate_name:sha(files[gate_name])},
        coordinator_and_worker_changed=False, unverified_machine_rejected=blocked_without_machine,
        CPU_checked=True, actual_GPU_inference=False, pending='One authorized save; live assigned hardware, window, model bytes, baselines and request gates before task runs.'))
    print('Authorized independent build frozen; no SaveKernel call performed.')


if __name__ == '__main__':
    main()
