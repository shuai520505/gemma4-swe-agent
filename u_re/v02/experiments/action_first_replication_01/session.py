"""Parameter-only adapter to GPU03's measured production coordinator.

The shared worker, native verifier, chroot, HTTP observer and model service are
unchanged. Both GPU batches and the external CPU transport enter this function.
"""
import types
from u_re.v01.experiments.action_priority_01.real_gemma_abba03 import session as proven
from .selection import HERE,ROOT

async def run(output,session_started,*,mode='GPU',cpu_transport=None,quota_at_dispatch=None,batch=1):
    assert type(batch) is int and batch in (1,2)
    source=__import__('pathlib').Path(proven.__file__).read_text(encoding='utf-8')
    substitutions={
        "HERE=Path(__file__).resolve().parent\nPRIOR=HERE.parent/'integrated_cpu_01'\nROOT=HERE.parents[4]":"HERE=STUDY;PRIOR=PINNED_PRIOR;ROOT=REPOSITORY",
        "from ..integrated_cpu_01.agent_phase import SubprocessManager":"from u_re.v01.experiments.action_priority_01.integrated_cpu_01.agent_phase import SubprocessManager",
        "from .ISOLATION_CANARY import CANARY":"from u_re.v01.experiments.action_priority_01.real_gemma_abba03.ISOLATION_CANARY import CANARY",
        "(PRIOR/'ABBA_EXPERIMENT_LOCK.json')":"(HERE/'EXPERIMENT_LOCK.json')",
        "(HERE/'ADMISSION_RECONCILIATION.json')":"(HERE/'SELECTED_TASKS.json')",
        "(HERE/'GPU_AUTHORIZATION.json')":"(HERE/('GPU_BATCH_%02d_AUTHORIZATION.json'%BATCH))",
        "grant['order']==lock['order']":"grant['order']==[r for r in lock['order'] if r['batch']==BATCH]",
        "admitted['status']=='EVIDENCE_RECONCILED_TWO_TASKS_ADMITTED'":"admitted['status']=='FOUR_TASKS_ADMITTED'",
        "[r['instance_id'] for r in admitted['tasks']]==['fastapi_9425','fastapi_14786']":"[r['instance_id'] for r in admitted['tasks']]==[t['instance_id'] for t in lock['tasks']] and len(lock['tasks'])==4",
        "execution_order=lock['order'] if mode=='GPU'":"execution_order=grant['order'] if mode=='GPU'",
        "frozen={t['instance_id']:t for t in lock['tasks']}":"frozen={t['instance_id']:t for t in lock['tasks'] if mode=='CPU_DRY_RUN' or t['instance_id'] in {r['instance_id'] for r in grant['order']}}",
        "native_real_baselines=['fastapi_9425','fastapi_14786']":"native_real_baselines=list(frozen)",
        "'GPU03_REAL_GEMMA_ABBA_COMPLETE'":"'V02_BATCH_REAL_GEMMA_COMPLETE'",
        "'GPU03_PAYLOAD_END_TO_END_CPU_PASS'":"'V02_PAYLOAD_END_TO_END_CPU_PASS'",
    }
    for old,new in substitutions.items():
        assert old in source,('GPU03 adapter source contract changed',old)
        source=source.replace(old,new)
    module=types.ModuleType(__package__+'.accepted_gpu03_coordinator')
    module.__file__=proven.__file__;module.__package__=__package__
    module.STUDY=HERE;module.REPOSITORY=ROOT;module.PINNED_PRIOR=ROOT/'u_re/v01/experiments/action_priority_01/integrated_cpu_01';module.BATCH=batch
    exec(compile(source,module.__file__,'exec'),module.__dict__)
    return await module.run(output,session_started,mode=mode,cpu_transport=cpu_transport,quota_at_dispatch=quota_at_dispatch)
