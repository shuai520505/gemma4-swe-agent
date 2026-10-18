"""CPU: unmodified public Requests snapshot, import correction and fixture gate."""
import json
from pathlib import Path
import re
import shlex

from harness_v2.evidence import Journal,atomic_json
from s1.task_identity import find_data,identify
from s1.util import sha_file
from .environment import SubprocessManager,install_editable


def check(output):
    from swegemma.deduplication import resolve_task_snapshot_paths
    from swegemma.harness.container_setup import extract_snapshot
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    data=find_data();atomic_json(output/'task_identity.json',identify(data,['requests_7328']))
    from adk_submission import ModelRegistry
    from swegemma.config import EvalConfig
    from swegemma.harness.container_setup import resolve_sandbox_setup_script
    resolved_setup=resolve_sandbox_setup_script(EvalConfig(tasks_path=data/'tasks.jsonl',snapshots_dir=data/'snapshots',
        wheels_dir=data/'wheels',results_dir=output/'unused',models=ModelRegistry(),sandbox='subprocess',
        submission_dir=Path(__file__).resolve().parents[1]/'candidates/control'))
    atomic_json(output/'official_setup_resolution.json',dict(path=str(resolved_setup) if resolved_setup else None,
        source_sha256=sha_file(resolved_setup) if resolved_setup else None,
        executed=False,reason='Inspect only; no unreviewed setup script may change original tests'))
    if resolved_setup:
        from harness_v2.evidence import atomic_bytes
        atomic_bytes(output/'official_sandbox_setup.py',resolved_setup.read_bytes())
    rows={r['instance_id']:r for r in map(json.loads,(data/'tasks.jsonl').read_text().splitlines())}
    row=rows['requests_7328']
    snapshot,base,overlay=resolve_task_snapshot_paths(data/'snapshots','requests_7328',row['repo'])
    manager=SubprocessManager(journal=Journal(output),base_dir=output/'sandboxes',timeout_seconds=180,task_wheels=data/'wheels')
    sid=manager.start()
    def execute(label,command,timeout=180):
        result=manager.exec(sid,command,timeout=timeout)
        atomic_json(output/(label+'.json'),dict(command=command,exit_code=result.exit_code,
            stdout=result.stdout,stderr=result.stderr))
        return result
    try:
        extract_snapshot(manager,sid,snapshot,base_snapshot_path=base,patch_path=overlay)
        workspace=manager.sandboxes[sid]['workspace']
        before={p.relative_to(workspace).as_posix():sha_file(p) for folder in ('src','tests')
            for p in sorted((workspace/folder).rglob('*.py'))}
        head=execute('base_commit','git rev-parse HEAD')
        assert head.exit_code==0
        # Curated task archives can retain an embedded synthetic Git HEAD.
        # Never checkout/reset it to force metadata equality. Pin actual archive
        # bytes and report the discrepancy as an additional endpoint limitation.
        embedded_head=head.stdout.strip()
        execute('embedded_git_metadata','git log -1 --format="%H%n%s%n%ct" && git status --porcelain')
        import hashlib
        pins=json.loads(Path(__file__).with_name('upstream_blob_pins.json').read_text())
        blobs={}
        for name,expected in pins['git_blob_sha1'].items():
            content=(workspace/name).read_bytes()
            blobs[name]=hashlib.sha1(b'blob '+str(len(content)).encode()+b'\0'+content).hexdigest()
            assert blobs[name]==expected,'Official archive file differs from declared upstream baseline: '+name
        probe="python3 -c 'import json,sys,requests,requests.sessions; print(json.dumps(dict(sys_path=sys.path,requests_file=requests.__file__,sessions_file=requests.sessions.__file__)))'"
        wrong=execute('before_editable',probe)
        assert wrong.exit_code==0
        install_editable(manager,sid)
        corrected=execute('after_editable',probe)
        assert corrected.exit_code==0
        provenance=json.loads(corrected.stdout)
        assert Path(provenance['sessions_file']).resolve().is_relative_to((workspace/'src').resolve())
        trace=execute('plugin_trace','python3 -m pytest --trace-config --collect-only -q tests/test_requests.py')
        assert trace.exit_code==0
        from .import_audit import install
        site=Path(install(manager.sandboxes[sid]['venv'])['site'])
        (site/'_s1_fixture_trace.py').write_bytes(Path(__file__).with_name('fixture_trace.py').read_bytes())
        execute('fixture_callchain','export S1_FIXTURE_TRACE='+shlex.quote(str(output/'fixture_callchain.jsonl'))+
            '; python3 -m pytest -p _s1_fixture_trace --setup-show -vv tests/test_requests.py -k test_no_content_length --maxfail=1')
        # Same native Phase-2 pytest semantics, but only original public baseline
        # tests: neither the historical Agent Patch nor evaluation test patch.
        command='PYTHONSAFEPATH=1 PYTHONNOUSERSITE=1 python3 -s -m pytest tests/test_requests.py -p no:anyio -o timeout=0 -o python_classes="Test* *Test" -q'
        result=execute('clean_baseline_pytest',command,timeout=300)
        errors=len(re.findall('ERROR at setup',result.stdout))
        providers=execute('provider_admission',"python3 -c 'import json,importlib.util,importlib.metadata as m; print(json.dumps(dict(modules={n:bool(importlib.util.find_spec(n)) for n in [\"pytest_httpbin\",\"httpbin\",\"trustme\"]},pytest11=[dict(name=e.name,value=e.value) for e in m.entry_points(group=\"pytest11\")])))'")
        available=json.loads(providers.stdout)
        resolver=execute('offline_dependency_resolution','python3 -m pip install --dry-run --no-index --find-links='+shlex.quote(str(data/'wheels'))+' pytest-httpbin==2.1.0')
        after={p.relative_to(workspace).as_posix():sha_file(p) for folder in ('src','tests')
            for p in sorted((workspace/folder).rglob('*.py'))}
        assert before==after,'Source or tests changed during infrastructure check'
        eligible=result.exit_code==0 and bool(available['modules'].get('pytest_httpbin'))
        report=dict(clean_base=row['base_commit'],Agent_patch_used=False,evaluation_test_patch_used=False,
            embedded_git_head=embedded_head,embedded_git_head_matches_declared_base=embedded_head==row['base_commit'],
            critical_upstream_blobs_verified=blobs,
            baseline_authority='Official registered archive bytes; embedded Git graph not asserted equal to task metadata',
            source_and_test_hashes_unchanged=True,files_checked=len(before),
            source_import_corrected=True,before_import=json.loads(wrong.stdout),after_import=provenance,
            pytest_exit_code=result.exit_code,fixture_setup_errors=errors,providers=available,
            offline_provider_resolvable=resolver.exit_code==0,requests_verifier_eligible=eligible,
            status='eligible' if eligible else 'blocked',
            blocker=None if eligible else 'Official offline wheel/input environment lacks required fixture providers; do not use Requests as a repair-rate endpoint')
        atomic_json(output/'environment_gate.json',report)
        return report
    finally:
        manager.cleanup_all()
        atomic_json(output/'cleanup.json',dict(cleanup_complete=not manager.sandboxes,
            remaining_directories=[str(p) for p in (output/'sandboxes').glob('swegemma_sandbox_*')]))
