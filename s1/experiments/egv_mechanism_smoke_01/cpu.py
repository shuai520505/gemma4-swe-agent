"""Selected clean FastAPI native Phase2; no Agent, reference repair or GPU."""
import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import unittest
from harness_v2.evidence import Journal, atomic_json
from s1.util import sha, sha_file
from s1.verifier_v3.audit import audit_verifier
from s1.verifier_v3.environment import SubprocessManager as NativeManager, research_environment

HERE = Path(__file__).resolve().parent


class SubprocessManager(NativeManager):
    """Passive host-side file capture; exact native pytest command unchanged."""
    def exec(self, sandbox_id, command, *, timeout=None):
        if sandbox_id != self.agent_id and ' -m pytest ' in command:
            workspace = self.sandboxes[sandbox_id]['workspace']
            paths = self.target_test_files
            atomic_json(self.journal.directory/'test_overlay_before_pytest.json', {
                'files': {n: {'present': (workspace/n).is_file(),
                              'sha256': sha_file(workspace/n) if (workspace/n).is_file() else None}
                          for n in paths},
                'native_command': command,
                'observer': 'Host reads only; no extra command, test or environment mutation'})
        return super().exec(sandbox_id, command, timeout=timeout)


async def phase2(output):
    from adk_submission import ModelRegistry
    from swegemma.models import load_tasks
    from swegemma.config import EvalConfig
    from swegemma.deduplication import resolve_task_snapshot_paths
    from swegemma.harness.verification import verify_task
    from s1.task_identity import find_data, identify
    output = Path(output); output.mkdir(parents=True, exist_ok=False)
    selected = json.loads((HERE/'selection.json').read_text()); data = find_data()
    task = next(t for t in load_tasks(data/'tasks.jsonl') if t.instance_id == selected['instance_id'])
    identity = identify(data, [task.instance_id]); actual = identity[task.instance_id]
    for key in ('base_commit', 'issue_sha256', 'task_record_sha256', 'test_patch_sha256'):
        assert actual[key] == selected[key], key
    assert actual['input_files'] == selected['input_files'], 'Snapshot drift'
    atomic_json(output/'task_inputs.json', identity)
    atomic_json(output/'official_verifier_source.json', {
        'verify_task_source': __import__('inspect').getsource(verify_task),
        'file': __import__('inspect').getfile(verify_task),
        'versions': {n: __import__('importlib.metadata', fromlist=['version']).version(n)
                     for n in ('swegemma','adk-submission','google-adk','litellm','pytest','pydantic','starlette','httpx')},
        'installed_pytest_entrypoints':[{ 'name':e.name,'value':e.value,'distribution':e.dist.name,'version':e.dist.version}
            for e in __import__('importlib.metadata',fromlist=['entry_points']).entry_points(group='pytest11')],
        'native_disabled_plugin':'anyio (exact official command) - installed entrypoints do not prove every plugin was loaded'})
    snapshot, base, overlay = resolve_task_snapshot_paths(data/'snapshots', task.instance_id, task.repo)
    manager = SubprocessManager(journal=Journal(output), base_dir=output/'sandbox_tmp',
        audit_modules=['fastapi','starlette','pydantic','pytest','httpx'], task_wheels=data/'wheels', timeout_seconds=120)
    manager.agent_id = 'evaluator_only'
    manager.target_test_files = list(task.test_files)
    cfg = EvalConfig(tasks_path=data/'tasks.jsonl', snapshots_dir=data/'snapshots', results_dir=output/'native',
        submission_dir=Path('s1/candidates/control'), models=ModelRegistry(), sandbox='subprocess',
        wheels_dir=data/'wheels', verification_timeout_seconds=300, enable_sandbox_testing=True, display_mode='quiet')
    try:
        with research_environment(audit_modules=manager.audit_modules, task_wheels=data/'wheels'):
            result = await verify_task(manager,cfg,task,snapshot,base_snapshot_path=base,patch_path=overlay,
                agent_patch='',start_time=time.perf_counter())
        atomic_json(output/'official_result.json',result.model_dump(mode='json',exclude={'trace'}))
    finally:
        manager.cleanup_all()
        cleanup = not manager.sandboxes and not list((output/'sandbox_tmp').glob('swegemma_sandbox_*'))
        atomic_json(output/'cleanup.json',dict(complete=cleanup))
    classification = audit_verifier(output); atomic_json(output/'structured_verifier.json',classification)
    capture = json.loads((output/'phase2_junit_capture.json').read_text()) if (output/'phase2_junit_capture.json').is_file() else {}
    overlay_proof = json.loads((output/'test_overlay_before_pytest.json').read_text()) if (output/'test_overlay_before_pytest.json').is_file() else {}
    files_present = bool(overlay_proof) and all(x['present'] for x in overlay_proof['files'].values())
    records = [json.loads(p.read_text()) for p in (output/'import_audit').rglob('*.json')]
    atomic_json(output/'import_record_index.json',dict(files=len(records),paths=[str(p.relative_to(output)) for p in (output/'import_audit').rglob('*.json')]))
    eligible = not classification['infrastructure_stop'] and classification['category'] in ('passed','assertion_failure') and cleanup and files_present
    admission = dict(instance_id=task.instance_id,base_commit=task.base_commit,eligible=eligible,
        structured_category=classification['category'],test_counts=classification.get('counts'),cleanup_complete=cleanup,
        original_native_JUnit=True,reference_patch_used=False,evaluator_test_patch_only=True,
        production_source_hashes=capture.get('production_source_hashes',{}),JUnit_sha256=capture.get('sha256'),
        test_files=list(task.test_files),target_test_files_present_before_native_pytest=files_present,
        scope='Unrepaired native Phase2; no Agent or alternate test run; no reference fix')
    atomic_json(output/'environment_admission.json',admission)
    assert admission['eligible'], 'Selected native baseline blocked; no model startup or task replacement'
    return admission


def main(output):
    output = Path(output); output.mkdir(parents=True,exist_ok=False)
    # P0 is first, independently persisted even when admission fails.
    admission = asyncio.run(phase2(output/'selected_baseline'))
    atomic_json(output/'cpu_gate.json',dict(passed=False,baseline=admission,compatibility='not_run',GPU=False))
    assert admission['eligible'], 'Selected task native baseline blocked; no GPU or replacement'
    proc = subprocess.run([sys.executable,'-m','s1.experiments.e3_structured_smoke_04.cpu',str(output/'frozen113')],capture_output=True,text=True,timeout=2600)
    (output/'frozen113.stdout.log').write_text(proc.stdout);(output/'frozen113.stderr.log').write_text(proc.stderr)
    gate = json.loads((output/'frozen113/cpu_gate.json').read_text())
    assert proc.returncode==0 and gate['passed'] and gate['tests_run']==113
    os.environ['EGV_CPU_EVIDENCE']=str(output/'candidate');(output/'candidate').mkdir()
    with (output/'candidate_tests.log').open('x') as log:
        tests=unittest.TextTestRunner(stream=log,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromName('s1.egv_v01.tests.CandidateTests'))
    candidate=dict(passed=tests.wasSuccessful() and not tests.skipped,tests_run=tests.testsRun,
        failures=len(tests.failures),errors=len(tests.errors),skipped=len(tests.skipped))
    # Import coordinator and parse the actual uploaded new Python files; no GPU.
    from .session import require_cpu
    import ast
    for path in HERE.glob('*.py'): ast.parse(path.read_text(),filename=str(path))
    final_gate=dict(passed=candidate['passed'],tests_run=113+tests.testsRun,
        baseline=admission,frozen113=gate,candidate=candidate,real_Runner=True,mocked_HTTP=True,GPU=False,
        source_hashes=json.loads(Path('s1/registration.json').read_text())['source_hashes'])
    atomic_json(Path('s1/cpu_gate.json'),final_gate)
    require_cpu(Path.cwd())
    atomic_json(output/'cpu_gate.json',final_gate)
    assert candidate['passed'] and tests.testsRun==2


if __name__=='__main__': main(sys.argv[1])
