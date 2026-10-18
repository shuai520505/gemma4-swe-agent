"""Full CPU replay plus evaluator-only unmodified Rich Phase2 readiness."""
import asyncio
import json
from pathlib import Path
import re
import subprocess
import sys
import time
import unittest
from harness_v2.evidence import Journal,atomic_json


async def phase2(output):
    from adk_submission import ModelRegistry
    from swegemma.models import load_tasks
    from swegemma.config import EvalConfig
    from swegemma.deduplication import resolve_task_snapshot_paths
    from swegemma.harness.verification import verify_task
    from s1.task_identity import find_data,identify
    from s1.infrastructure_recovery.environment import SubprocessManager,research_environment
    output=Path(output);output.mkdir(parents=True,exist_ok=False);data=find_data()
    task=next(t for t in load_tasks(data/'tasks.jsonl') if t.instance_id=='rich_3278')
    draft=json.loads(Path('s1/infrastructure_recovery/next_experiment_plan.json').read_text())
    expected=next(r for r in draft['pairs'] if r['instance_id']==task.instance_id)
    assert task.base_commit==expected['base_commit']
    snapshot,base,overlay=resolve_task_snapshot_paths(data/'snapshots',task.instance_id,task.repo)
    atomic_json(output/'task_inputs.json',identify(data,[task.instance_id]))
    manager=SubprocessManager(journal=Journal(output),base_dir=output/'sandbox_tmp',
        audit_modules=['rich','rich.ansi'],task_wheels=data/'wheels',timeout_seconds=120)
    manager.agent_id='evaluator_only'
    cfg=EvalConfig(tasks_path=data/'tasks.jsonl',snapshots_dir=data/'snapshots',results_dir=output/'native',
        submission_dir=Path('s1/candidates/control'),models=ModelRegistry(),sandbox='subprocess',wheels_dir=data/'wheels',
        verification_timeout_seconds=300,enable_sandbox_testing=True,display_mode='quiet')
    try:
        with research_environment(audit_modules=['rich','rich.ansi'],task_wheels=data/'wheels'):
            result=await verify_task(manager,cfg,task,snapshot,base_snapshot_path=base,patch_path=overlay,
                agent_patch='',start_time=time.perf_counter())
        raw=result.model_dump(mode='json',exclude={'trace'})
        atomic_json(output/'official_result.json',raw)
        native=json.loads((output/'phase2_execution.json').read_text())
        text=native['stdout']+'\n'+native['stderr']
        passed=native['exit_code'] in (0,1) and bool(re.search(r'\b\d+ passed\b',text))
        passed=passed and not re.search(r'\bERROR\b|\b\d+ errors?\b|INTERNALERROR|ModuleNotFoundError',text)
        admission=dict(instance_id=task.instance_id,base_commit=task.base_commit,eligible=bool(passed),
            native_phase2_completed=True,unrepaired_baseline=True,reference_patch_used=False,
            evaluator_test_patch_applied_by_official_verifier=True,test_files=list(task.test_files),
            test_exit_code=native['exit_code'],raw_resolved=result.resolved,
            scope='Environment readiness only; expected baseline assertion failure is not Agent failure')
    finally:
        manager.cleanup_all()
    admission['cleanup_complete']=not manager.sandboxes and not list((output/'sandbox_tmp').glob('swegemma_sandbox_*'))
    admission['eligible']=admission['eligible'] and admission['cleanup_complete']
    atomic_json(output/'environment_admission.json',admission)
    assert admission['eligible'],'Full official Rich Phase2 environment blocked'
    return admission


def main(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    child=subprocess.run([sys.executable,'-m','s1.infrastructure_recovery.cpu',str(output/'recovery97')],
        capture_output=True,text=True,timeout=1800)
    (output/'recovery.stdout.log').write_text(child.stdout);(output/'recovery.stderr.log').write_text(child.stderr)
    gate=json.loads((output/'recovery97/cpu_gate.json').read_text())
    assert child.returncode==0 and gate['passed'] and gate['tests_run']==97
    suite=unittest.defaultTestLoader.loadTestsFromName('s1.experiments.e3_localize_smoke_03.test_idle')
    with (output/'idle_tests.log').open('x') as log:tests=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    assert tests.wasSuccessful() and not tests.skipped
    admission=asyncio.run(phase2(output/'rich_full_phase2'))
    final=dict(gate,tests_run=97+tests.testsRun,new_idle_tests=tests.testsRun,legacy_count=38,
        Rich_full_phase2_environment=admission,real_official_Runner=True,Gemma_inference=False,GPU=False)
    atomic_json(output/'cpu_gate.json',final)
    print(json.dumps({k:v for k,v in final.items() if k!='source_hashes'},indent=2))


if __name__=='__main__':main(sys.argv[1])
