"""Freeze a non-executable experiment template; never dispatch or grant permission."""
import json
from .build import HERE, ROOT, frozen_write, sha, build


def freeze():
    candidates=build()
    historical=json.loads((ROOT/'meer/v01/gpu01/EXECUTION_MANIFEST.json').read_bytes())
    selected=json.loads((HERE/'SELECTED_TASKS.json').read_bytes())
    assert selected['selected_count']==0
    slots=[]
    for number,(task,arm) in enumerate((('T1','N'),('T1','D'),('T2','D'),('T2','N')),1):
        slots.append(dict(run=number,task_slot=task,instance_id=None,task_identity=None,arm=arm,
            candidate_ZIP_sha256=candidates['arms'][arm]['ZIP_sha256'],
            status='NOT_RUN',native_resolved=None,model_requests=None,received_tokens=None))
    lock=dict(experiment='EGRD-V022-MEER-ADOPTION',status='TEMPLATE_NOT_EXECUTABLE_TASK_AND_CPU_GATES_BLOCKED',
        factor='Direct invocation cue vs neutral availability; identical active verifier',sessions=slots,
        source_base_PR35='765530b39a7666a78ece099756fac925a932c617',
        candidate_manifest_sha256=sha((HERE/'CANDIDATE_MANIFEST.json').read_bytes()),
        task_pool_lock_sha256=sha((HERE/'TASK_POOL_LOCK.json').read_bytes()),
        selected_tasks_sha256=sha((HERE/'SELECTED_TASKS.json').read_bytes()),
        model=historical['model'],expected_environment_lock_sha256=historical['environment_lock_sha256'],
        original_execution_manifest_sha256=sha((ROOT/'meer/v01/gpu01/EXECUTION_MANIFEST.json').read_bytes()),
        budget=dict(context=32768,output=16384,safety=1024,input_cap=15360,thinking=4096,seed=17,
                    Agent_seconds=300,charged_tools=60,command_seconds=120,include_thoughts='omitted_unchanged'),
        production_payload_sha256=None,production_entry_source_commit=None,
        maximum_proposed_GPU_Notebooks=1,maximum_requested_window_seconds=10000,maximum_real_sessions=4,
        actual_resource_gate='NOT_QUERIED_NOT_AUTHORIZED',full_CPU_acceptance='FULL_COMPILER_CPU_ACCEPTANCE_NOT_RUN',
        owner_authorization='NOT_GRANTED_PREPARATION_ONLY',actual_GPU_inference=0,actual_Notebook_saves=0,
        formal_submission=False,readiness=False,
        task_admission='BLOCKED_NO_INDEPENDENT_TASKS_IN_AVAILABLE_SOURCE',
        freeze_limit='Candidate hashes, budget and slot order frozen; task/session production identity is NOT complete')
    frozen_write(HERE/'GPU_EXECUTION_LOCK.json',(json.dumps(lock,indent=2,sort_keys=True)+'\n').encode())
    return lock


if __name__=='__main__':
    freeze()
    print('Template frozen; readiness=False; no dispatch.')
