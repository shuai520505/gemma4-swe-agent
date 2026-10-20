"""Evaluator-only clean baseline and input hashes. Never runs any Agent/model."""
import asyncio
import hashlib
import json
from pathlib import Path
import sys
import time
from harness_v2.evidence import Journal,atomic_json


async def run(output):
    from adk_submission import ModelRegistry
    from swegemma.models import load_tasks
    from swegemma.config import EvalConfig
    from swegemma.deduplication import resolve_task_snapshot_paths
    from swegemma.harness.verification import verify_task
    from s1.task_identity import find_data,identify
    from s1.verifier_v3.environment import SubprocessManager,research_environment
    from s1.verifier_v3.audit import audit_verifier
    import torch
    assert sys.platform=='linux' and torch.cuda.device_count()==0
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    here=Path(__file__).resolve().parent
    selection=json.loads((here/'GPU_TASK_SELECTION_DRAFT.json').read_text())
    data=find_data();tasks={t.instance_id:t for t in load_tasks(data/'tasks.jsonl')}
    identities=identify(data,[r['instance_id'] for r in selection['selected']])
    atomic_json(output/'task_identities.json',identities)
    results=[]
    for row in selection['selected']:
        ident=row['instance_id'];identity=identities[ident]
        assert identity['base_commit']==row['base_commit'] and identity['issue_sha256']==row['issue_sha256']
        task=tasks[ident];directory=output/ident;directory.mkdir()
        snapshot,base,overlay=resolve_task_snapshot_paths(data/'snapshots',ident,task.repo)
        prefix=task.repo.split('/')[-1]
        journal=Journal(directory);manager=SubprocessManager(journal=journal,base_dir=directory/'sandbox_tmp',
            audit_modules=[prefix],task_wheels=data/'wheels',timeout_seconds=120)
        manager.agent_id='evaluator_only'
        config=EvalConfig(tasks_path=data/'tasks.jsonl',snapshots_dir=data/'snapshots',results_dir=directory/'native',
            submission_dir=here/'candidate_noegv',models=ModelRegistry(),sandbox='subprocess',wheels_dir=data/'wheels',
            verification_timeout_seconds=300,enable_sandbox_testing=True,display_mode='quiet')
        try:
            with research_environment(audit_modules=[prefix],task_wheels=data/'wheels'):
                result=await verify_task(manager,config,task,snapshot,base_snapshot_path=base,patch_path=overlay,
                    agent_patch='',start_time=time.perf_counter())
            atomic_json(directory/'official_result.json',result.model_dump(mode='json',exclude={'trace'}))
        finally:
            manager.cleanup_all()
        audit=audit_verifier(directory)
        atomic_json(directory/'structured_verifier.json',audit)
        cleanup=not manager.sandboxes and not list((directory/'sandbox_tmp').glob('swegemma_sandbox_*'))
        capture=json.loads((directory/'phase2_junit_capture.json').read_text()) if (directory/'phase2_junit_capture.json').exists() else {}
        # A fully passing unrepaired base is not a discriminating repair endpoint.
        eligible=not audit['infrastructure_stop'] and audit['category']=='assertion_failure' and cleanup and capture.get('status')=='captured'
        info=dict(instance_id=ident,eligible=eligible,category=audit['category'],counts=audit.get('counts'),
            clean_baseline_resolved=result.resolved,official_test_exit_code=result.test_exit_code,
            native_command_unchanged=True,agent_patch='',model_calls=0,reference_repair_used=False,
            cleanup_complete=cleanup,JUnit_sha256=capture.get('sha256'),
            scope='Evaluator-only original snapshot plus official evaluator test overlay. No Agent receives tests, outputs or repairs.')
        atomic_json(directory/'admission.json',info);results.append(info)
        if not eligible:
            break  # Fixed selected task cannot be replaced after environment failure.
    final=dict(passed=len(results)==len(selection['selected']) and all(r['eligible'] for r in results),
        proposed_tasks=len(selection['selected']),checked=results,not_run=[r['instance_id'] for r in selection['selected'] if r['instance_id'] not in {x['instance_id'] for x in results}],
        GPU=False,model_inference=False,Agent_runs=0,reference_repair_used=False,
        disposition='Admission diagnostics completed; failed environment/non-discriminating endpoint blocks GPU registration without task replacement.')
    atomic_json(output/'cpu_gate.json',final);print(json.dumps(final,indent=2),flush=True)
    # A diagnostic No-Go is still an accurately completed CPU inspection.
    return 0


if __name__=='__main__':
    asyncio.run(run(sys.argv[1]))
