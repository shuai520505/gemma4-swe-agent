"""CPU-only original native baseline + independent passive fixture diagnostics.

No Agent/model/reference repair. No test edits, provider injection or dependencies
from outside the frozen official offline caches. The old report is never updated.
"""
import asyncio
import hashlib
import importlib
import inspect
import json
from pathlib import Path
import shlex
import sys
import time

from harness_v2.evidence import Journal, atomic_bytes, atomic_json
from s1.task_identity import find_data, identify

HERE=Path(__file__).resolve().parent
IDENT='requests_7433'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def unchanged_inputs(workspace):
    # All original Python and dependency/config bytes, not generated caches/metadata.
    return {p.relative_to(workspace).as_posix():digest(p) for p in sorted(workspace.rglob('*'))
            if p.is_file() and not {'.git','__pycache__','.pytest_cache'}.intersection(p.relative_to(workspace).parts)
            and (p.suffix=='.py' or p.name in ('pyproject.toml','pytest.ini','setup.cfg','tox.ini')
                 or p.name.startswith('requirements')) and '.egg-info' not in str(p)}


async def run(output):
    import torch
    assert sys.platform=='linux' and torch.cuda.device_count()==0
    from adk_submission import ModelRegistry
    from swegemma.config import EvalConfig
    from swegemma.models import load_tasks
    from swegemma.deduplication import resolve_task_snapshot_paths
    from swegemma.harness.verification import verify_task
    from s1.verifier_v3.environment import SubprocessManager as NativeObserved, research_environment
    from s1.verifier_v3.audit import audit_verifier
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False)
    data=find_data()
    current=identify(data,[IDENT])[IDENT]
    expected=json.loads((HERE/'expected_task.json').read_text())
    assert current==expected, 'Task identity drift; do not proceed'
    atomic_json(output/'task_identity.json',current)
    # Source inspection only; no edits to package or setup/verification logic.
    for name in ('swegemma.harness.verification','swegemma.harness.container_setup','swegemma.sandbox.subprocess','_pytest.fixtures','_pytest.config'):
        m=importlib.import_module(name)
        atomic_bytes(output/'official_sources'/(name+'.py'),Path(inspect.getfile(m)).read_bytes())
    task={t.instance_id:t for t in load_tasks(data/'tasks.jsonl')}[IDENT]
    snapshot,base,overlay=resolve_task_snapshot_paths(data/'snapshots',IDENT,task.repo)
    journal=Journal(output/'native_baseline')
    diagnostics_done=[]
    class SubprocessManager(NativeObserved):
        # Keep organizer's required literal class name for unchanged native dispatch.
        def exec(self,sid,command,*,timeout=None):
            if ' -m pytest ' in command:
                workspace=self.sandboxes[sid]['workspace']
                if not (output/'before_native_files.json').exists():
                    atomic_json(output/'before_native_files.json',unchanged_inputs(workspace))
            return super().exec(sid,command,timeout=timeout)

        def stop(self,sid):
            if sid in self.sandboxes and sid not in diagnostics_done and sid in self.junit_paths:
                diagnostics_done.append(sid)
                # Native command has returned. Additional commands cannot replace its result.
                diag=output/'diagnostics';diag.mkdir()
                workspace=self.sandboxes[sid]['workspace']
                files=unchanged_inputs(workspace)
                atomic_json(output/'after_native_files.json',files)
                before=json.loads((output/'before_native_files.json').read_text())
                assert before==files,'Native baseline unexpectedly changed source/test/config bytes'
                for name in ('tests/conftest.py','tests/test_requests.py','pyproject.toml','pytest.ini','setup.cfg','setup.py','tox.ini'):
                    p=workspace/name
                    if p.exists():atomic_bytes(diag/'configuration'/name,p.read_bytes())
                atomic_json(diag/'conftest_hierarchy.json',[dict(path=p.relative_to(workspace).as_posix(),sha256=digest(p)) for p in workspace.rglob('conftest.py')])
                def execute(label,command,timeout=120):
                    start=time.monotonic()
                    # Bypass ONLY research Phase2 observers for these explicitly
                    # separate probes. Otherwise an extra pytest command would
                    # overwrite native phase2_command/result evidence.
                    from swegemma.sandbox.subprocess import SubprocessManager as Organizer
                    r=Organizer.exec(self,sid,command,timeout=timeout)
                    atomic_json(diag/(label+'.json'),dict(command=command,exit_code=r.exit_code,
                                stdout=r.stdout,stderr=r.stderr,seconds=time.monotonic()-start,
                                scope='Independent post-native diagnostic; never used as the native TaskResult'))
                    return r
                inventory='''import sys,json,os,importlib.util,importlib.metadata as m
names=['pytest','pytest-httpbin','httpbin','trustme','pluggy','swegemma','adk-submission']
versions={}
for n in names:
    try:versions[n]=m.version(n)
    except m.PackageNotFoundError:versions[n]=None
eps=[dict(name=e.name,value=e.value,distribution=d.metadata['Name'],version=d.version,path=str(d._path)) for d in m.distributions() for e in d.entry_points if e.group=='pytest11']
mods={n:(str(s.origin) if (s:=importlib.util.find_spec(n)) else None) for n in ['pytest_httpbin','httpbin','trustme','requests']}
print(json.dumps(dict(python=sys.version,executable=sys.executable,sys_path=sys.path,versions=versions,modules=mods,pytest11=eps,environment={n:os.environ.get(n) for n in ['PYTEST_DISABLE_PLUGIN_AUTOLOAD','PYTEST_PLUGINS','PYTEST_ADDOPTS','PYTHONPATH','PYTHONSAFEPATH','PYTHONNOUSERSITE']})))
'''
                r=execute('environment','PYTHONSAFEPATH=1 PYTHONNOUSERSITE=1 python3 -s -c '+shlex.quote(inventory))
                assert r.exit_code==0
                execute('plugin_trace','PYTHONSAFEPATH=1 PYTHONNOUSERSITE=1 python3 -s -m pytest --trace-config --collect-only -q tests/test_requests.py -p no:anyio -o timeout=0 -o python_classes="Test* *Test"')
                # Dedicated read-only observer, installed only for this post-native probe.
                from s1.infrastructure_recovery.import_audit import install
                site=Path(install(self.sandboxes[sid]['venv'])['site'])
                atomic_bytes(site/'_ure_fixture_observer.py',(HERE/'observer.py').read_bytes())
                execute('fixture_lookup','URE_FIXTURE_TRACE='+shlex.quote(str(diag/'fixture_lookup.jsonl'))+
                        ' PYTHONSAFEPATH=1 PYTHONNOUSERSITE=1 python3 -s -m pytest -p _ure_fixture_observer --full-trace --setup-show -vv tests/test_requests.py -k test_no_content_length --maxfail=1 -p no:anyio -o timeout=0 -o python_classes="Test* *Test"')
                execute('explicit_provider_import','PYTHONSAFEPATH=1 PYTHONNOUSERSITE=1 python3 -s -m pytest -p pytest_httpbin.plugin --collect-only -q tests/test_requests.py')
                # No dependency download/install; only a failing offline resolver is permitted.
                paths=[data/'wheels',Path(json.loads((HERE/'runtime_paths.json').read_text())['wheelhouse'])]
                command='python3 -m pip install --dry-run --no-index --disable-pip-version-check '+ ' '.join('--find-links='+shlex.quote(str(p)) for p in paths)+' pytest-httpbin==2.1.0'
                execute('offline_provider_resolution',command)
                after=unchanged_inputs(workspace)
                atomic_json(output/'after_diagnostics_files.json',after)
                assert before==after,'A diagnostic modified source/test/config bytes'
            return super().stop(sid)
    manager=SubprocessManager(journal=journal,base_dir=output/'sandbox_tmp',audit_modules=['requests'],task_wheels=data/'wheels',timeout_seconds=120)
    manager.agent_id='no_agent_evaluator_only'
    config=EvalConfig(tasks_path=data/'tasks.jsonl',snapshots_dir=data/'snapshots',results_dir=output/'native_unused',
        submission_dir=HERE.parents[1]/'candidate_noegv',models=ModelRegistry(),sandbox='subprocess',
        wheels_dir=data/'wheels',verification_timeout_seconds=300,enable_sandbox_testing=True,display_mode='quiet')
    # HERE = .../v01/infrastructure/requests_7433_fixture_01; parents[1] = v01.
    try:
        from swegemma.harness.container_setup import resolve_sandbox_setup_script
        setup=resolve_sandbox_setup_script(config)
        atomic_json(output/'setup_resolution.json',dict(path=str(setup),executed=False,sha256=digest(setup) if setup else None))
        if setup:atomic_bytes(output/'official_sources/sandbox_setup.py',Path(setup).read_bytes())
        with research_environment(audit_modules=['requests'],task_wheels=data/'wheels'):
            result=await verify_task(manager,config,task,snapshot,base_snapshot_path=base,patch_path=overlay,
                                     agent_patch='',start_time=time.perf_counter())
        atomic_json(output/'native_baseline/official_result.json',result.model_dump(mode='json',exclude={'trace'}))
    finally:
        manager.cleanup_all()
        atomic_json(output/'cleanup.json',dict(complete=not manager.sandboxes,
                    remaining_directories=[str(p) for p in (output/'sandbox_tmp').glob('swegemma_sandbox_*')]))
    atomic_json(output/'native_baseline/structured_verifier.json',audit_verifier(output/'native_baseline'))
    # Inventory BOTH approved caches, including embedded entry point metadata.
    import zipfile
    inventories={}
    for label,cache in [('task',data/'wheels'),('official',Path(json.loads((HERE/'runtime_paths.json').read_text())['wheelhouse']))]:
        rows={}
        for p in sorted(cache.rglob('*.whl')):
            with zipfile.ZipFile(p) as z:
                names=[n for n in z.namelist() if n.endswith('.dist-info/entry_points.txt')]
                ep={n:z.read(n).decode(errors='replace') for n in names}
                provider_modules=[n for n in z.namelist() if n.startswith(('pytest_httpbin/','httpbin/','trustme/'))]
            rows[p.name]=dict(sha256=digest(p),bytes=p.stat().st_size,entry_points=ep,provider_modules=provider_modules)
        inventories[label]=rows
    atomic_json(output/'wheel_inventory.json',inventories)
    from .minimal import run as minimal
    toy=minimal(output/'minimal')
    atomic_json(output/'cpu_gate.json',dict(diagnostic_completed=True,synthetic_semantics_passed=toy['passed'],
                native_audit=audit_verifier(output/'native_baseline'),GPU=False,Agent_runs=0,model_calls=0,
                source_and_test_bytes_unchanged=True,reference_repair_used=False,
                official_environment_repair_applied=False,
                disposition='Diagnostic completion is not official baseline eligibility. Classify from raw evidence.'))
    return 0


if __name__=='__main__':
    raise SystemExit(asyncio.run(run(sys.argv[1])))
