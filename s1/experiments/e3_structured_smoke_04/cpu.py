"""Official CPU admission and unchanged native Phase2 on the selected base."""
import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import unittest
from harness_v2.evidence import Journal,atomic_json
from s1.util import sha_file
from s1.verifier_v3.audit import audit_verifier


async def phase2(output):
    from adk_submission import ModelRegistry
    from swegemma.models import load_tasks
    from swegemma.config import EvalConfig
    from swegemma.deduplication import resolve_task_snapshot_paths
    from swegemma.harness.verification import verify_task
    from s1.task_identity import find_data,identify
    from s1.verifier_v3.environment import SubprocessManager,research_environment
    output=Path(output);output.mkdir(parents=True,exist_ok=False);data=find_data()
    selected=json.loads(Path(__file__).with_name('selection.json').read_text())
    task=next(t for t in load_tasks(data/'tasks.jsonl') if t.instance_id==selected['instance_id'])
    inputs=identify(data,[task.instance_id]);identity=inputs[task.instance_id]
    assert identity['base_commit']==selected['base_commit'] and identity['issue_sha256']==selected['issue_sha256']
    atomic_json(output/'task_inputs.json',inputs)
    snapshot,base,overlay=resolve_task_snapshot_paths(data/'snapshots',task.instance_id,task.repo)
    manager=SubprocessManager(journal=Journal(output),base_dir=output/'sandbox_tmp',
        audit_modules=['rich'],task_wheels=data/'wheels',timeout_seconds=120)
    manager.agent_id='evaluator_only'
    cfg=EvalConfig(tasks_path=data/'tasks.jsonl',snapshots_dir=data/'snapshots',results_dir=output/'native',
        submission_dir=Path('s1/candidates/control'),models=ModelRegistry(),sandbox='subprocess',wheels_dir=data/'wheels',
        verification_timeout_seconds=300,enable_sandbox_testing=True,display_mode='quiet')
    try:
        with research_environment(audit_modules=['rich'],task_wheels=data/'wheels'):
            result=await verify_task(manager,cfg,task,snapshot,base_snapshot_path=base,patch_path=overlay,
                agent_patch='',start_time=time.perf_counter())
        atomic_json(output/'official_result.json',result.model_dump(mode='json',exclude={'trace'}))
    finally:manager.cleanup_all()
    classification=audit_verifier(output)
    atomic_json(output/'structured_verifier.json',classification)
    capture=json.loads((output/'phase2_junit_capture.json').read_text())
    eligible=not classification['infrastructure_stop'] and classification['category'] in ('passed','assertion_failure')
    # Baseline can fail the task assertions; it must still actually run tests.
    cleanup=not manager.sandboxes and not list((output/'sandbox_tmp').glob('swegemma_sandbox_*'))
    admission=dict(instance_id=task.instance_id,base_commit=task.base_commit,eligible=eligible and cleanup,
        structured_category=classification['category'],test_counts=classification.get('counts'),
        original_native_JUnit=True,reference_patch_used=False,evaluator_test_patch_only=True,
        cleanup_complete=cleanup,production_source_hashes=capture.get('production_source_hashes',{}),
        JUnit_sha256=capture.get('sha256'),test_files=list(task.test_files),
        scope='Clean unrepaired native Phase2; assertion failure is not environment failure')
    atomic_json(output/'environment_admission.json',admission)
    assert admission['eligible'],'Selected task full structured baseline gate failed; no replacement permitted'
    return admission


def replay(output):
    output=Path(output);fixtures=Path('s1/verifier_v3/fixtures')
    pins=json.loads((fixtures/'manifest.json').read_text());results={}
    for name in ('rich_historical.json','requests_historical.json'):
        assert sha_file(fixtures/name)==pins[name]['sha256']
        directory=output/name.removesuffix('.json');directory.mkdir(parents=True)
        (directory/'phase2_execution.json').write_bytes((fixtures/name).read_bytes())
        baseline=dict(environment_blocked_verified=True,matching_callchain_verified=True,
            proof=pins['requests_baseline.json']) if name.startswith('requests') else None
        result=audit_verifier(directory,baseline=baseline,historical_attestation={'phase2_sha256':pins[name]['sha256']})
        atomic_json(directory/'structured_verifier.json',result);results[name]=result
    atomic_json(output/'summary.json',results)


def main(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    native=subprocess.run([sys.executable,'-m','s1.experiments.e3_localize_smoke_03.cpu',str(output/'baseline100')],
        capture_output=True,text=True,timeout=2000)
    (output/'baseline.stdout.log').write_text(native.stdout);(output/'baseline.stderr.log').write_text(native.stderr)
    baseline=json.loads((output/'baseline100/cpu_gate.json').read_text())
    assert native.returncode==0 and baseline['passed'] and baseline['tests_run']==100
    os.environ['S1_V3_TEST_EVIDENCE']=str(output/'structured_cases')
    tests=unittest.defaultTestLoader.loadTestsFromName('s1.verifier_v3.tests')
    with (output/'structured_tests.log').open('x') as log:
        result=unittest.TextTestRunner(stream=log,verbosity=2).run(tests)
    replay(output/'historical_replay')
    test_gate=dict(passed=result.wasSuccessful() and not result.skipped,tests_run=100+result.testsRun,
        legacy_count=38,baseline_tests=100,structured_tests=result.testsRun,
        failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),
        real_official_Runner=True,versions=baseline['versions'],
        source_hashes=json.loads(Path('s1/registration.json').read_text())['source_hashes'])
    atomic_json(output/'controller_gate.json',test_gate)
    assert result.testsRun==json.loads(Path('s1/registration.json').read_text())['structured_test_count']
    assert test_gate['passed'],'Structured regression failed; GPU forbidden'
    admission=asyncio.run(phase2(output/'selected_baseline'))
    atomic_json(output/'cpu_gate.json',dict(test_gate,selected_baseline=admission,GPU=False,Gemma_inference=False))
    print(json.dumps({k:v for k,v in test_gate.items() if k!='source_hashes'},indent=2))


if __name__=='__main__':main(sys.argv[1])
