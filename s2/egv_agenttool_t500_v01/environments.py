"""Evaluator-only fresh baseline eligibility; no Agent and no repair reference."""
import asyncio
import hashlib
import json
from pathlib import Path
import sys
import time
from harness_v2.evidence import Journal, atomic_json
from s1.task_identity import find_data, identify
from s1.verifier_v3.audit import audit_verifier
from s1.verifier_v3.environment import SubprocessManager, research_environment

HERE=Path(__file__).resolve().parent


async def check(selected, output):
    from adk_submission import ModelRegistry
    from swegemma.models import load_tasks
    from swegemma.config import EvalConfig
    from swegemma.deduplication import resolve_task_snapshot_paths
    from swegemma.harness.verification import verify_task
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    data=find_data();task=next(t for t in load_tasks(data/'tasks.jsonl') if t.instance_id==selected['instance_id'])
    inputs=identify(data,[task.instance_id]);item=inputs[task.instance_id]
    assert item['base_commit']==selected['base_commit'] and item['issue_sha256']==selected['issue_sha256']
    atomic_json(output/'task_inputs.json',inputs)
    import importlib.metadata
    atomic_json(output/'host_versions.json',{n:importlib.metadata.version(n) for n in
        ('swegemma','adk-submission','google-adk','litellm','pytest','pydantic','starlette','httpx')})
    snapshot,base,overlay=resolve_task_snapshot_paths(data/'snapshots',task.instance_id,task.repo)
    module={'Textualize/rich':'rich','fastapi/fastapi':'fastapi','psf/requests':'requests','encode/httpx':'httpx'}[task.repo]
    manager=SubprocessManager(journal=Journal(output),base_dir=output/'sandbox_tmp',audit_modules=[module],task_wheels=data/'wheels',timeout_seconds=120)
    manager.agent_id='evaluator_only'
    cfg=EvalConfig(tasks_path=data/'tasks.jsonl',snapshots_dir=data/'snapshots',results_dir=output/'native',submission_dir=HERE/'candidate',
        models=ModelRegistry(),sandbox='subprocess',wheels_dir=data/'wheels',verification_timeout_seconds=300,enable_sandbox_testing=True,display_mode='quiet')
    error=None
    try:
        with research_environment(audit_modules=[module],task_wheels=data/'wheels'):
            result=await verify_task(manager,cfg,task,snapshot,base_snapshot_path=base,patch_path=overlay,agent_patch='',start_time=time.perf_counter())
        atomic_json(output/'official_result.json',result.model_dump(mode='json',exclude={'trace'}))
    except Exception as exc:
        import traceback
        error=repr(exc);atomic_json(output/'exception.json',dict(error=error,traceback=traceback.format_exc()))
    finally:
        manager.cleanup_all()
        cleanup=not manager.sandboxes and not list((output/'sandbox_tmp').glob('swegemma_sandbox_*'))
        atomic_json(output/'cleanup.json',dict(complete=cleanup))
    classification=audit_verifier(output)
    atomic_json(output/'structured_verifier.json',classification)
    cap=output/'phase2_junit_capture.json';capture=json.loads(cap.read_text()) if cap.exists() else {}
    eligible=not error and not classification['infrastructure_stop'] and classification['category'] in ('passed','assertion_failure') and cleanup
    admission=dict(**selected,eligible=bool(eligible),cleanup_complete=cleanup,error=error,
        category=classification['category'],counts=classification.get('counts'),original_JUnit_sha256=capture.get('sha256'),
        production_source_hashes=capture.get('production_source_hashes',{}),input_files=item['input_files'],
        reference_patch_used=False,Agent_executed=False,scope='Clean baseline only; ordinary feature test-call failures allowed; setup/collection/execution/unknown block eligibility.')
    atomic_json(output/'environment_admission.json',admission)
    return admission


def main(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    from .session import require_cpu,require_authorization
    require_cpu(Path.cwd())
    try:require_authorization(dict(status='DRAFT'),dict(authorized=False),1)
    except AssertionError:pass
    else:raise AssertionError('Draft accidentally admitted GPU execution')
    atomic_json(output/'draft_execution_guard.json',dict(passed=True,GPU_started=False))
    # Exercise the exact observer registration used by the research worker,
    # in addition to CPU04's empty-State and native Runner fixture paths.
    from .tests.runner_cases import exercise
    actual=asyncio.run(exercise('closed_loop',output/'research_observer_integration',native=True,research_observer=True))
    assert actual['closed_loop'] and actual['explicit_submit'] and actual['HTTP']['passed']
    from .nested_metrics import inspect_nested
    nested=inspect_nested(output/'research_observer_integration')
    atomic_json(output/'research_observer_integration/nested_metrics.json',nested)
    assert len(nested['delegations'])==2 and not nested['child_workspace_side_effects']
    negative=asyncio.run(exercise('child_write',output/'research_side_effect_negative'))
    negative_audit=inspect_nested(output/'research_side_effect_negative')
    atomic_json(output/'research_side_effect_negative/nested_metrics.json',negative_audit)
    assert negative_audit['child_workspace_side_effects']
    import unittest
    with (output/'statistics_tests.log').open('x') as log:
        stats=unittest.TextTestRunner(stream=log,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromName('s2.egv_agenttool_t500_v01.tests.test_statistics'))
    assert stats.wasSuccessful() and not stats.skipped
    pool=json.loads((HERE/'TASK_POOL_PREREGISTRATION.json').read_text())
    assert not pool['GPU_authorized']
    records=[]
    for selected in pool['pool']:
        records.append(asyncio.run(check(selected,output/selected['instance_id'])))
        atomic_json(output/'screening_progress.json',records)
        # A cleanup failure is not merely an ineligible task: stop this CPU
        # process rather than risk contaminating subsequent sandboxes.
        if not records[-1]['cleanup_complete']:break
    chosen=[];counts={}
    for r in records:
        if r['eligible'] and counts.get(r['repo'],0)<4 and len(chosen)<8:
            chosen.append(r);counts[r['repo']]=counts.get(r['repo'],0)+1
    complete=len(records)==len(pool['pool']) and all(r['cleanup_complete'] for r in records)
    gate=dict(passed=complete and len(chosen)==8,screening_complete=complete,selected=chosen,records=records,
        pool_sha256=hashlib.sha256((HERE/'TASK_POOL_PREREGISTRATION.json').read_bytes()).hexdigest(),
        GPU=False,Agent_runs=0,eligibility_only=True)
    atomic_json(output/'environment_gate.json',gate)
    print(json.dumps(dict(passed=gate['passed'],screened=len(records),selected=[r['instance_id'] for r in chosen]),indent=2))


if __name__=='__main__':main(sys.argv[1])
