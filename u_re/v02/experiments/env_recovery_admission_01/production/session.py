"""Minimal task/environment adaptation of the CPU- and GPU-proven GPU03 Session.

The official Runner, worker, tools, verifier and chroot implementation are reused
byte-for-byte. CPU transport is supplied externally, never in the production ZIP.
This preparation has no matching GPU authorization, so GPU entry fails closed.
"""
import inspect,json,time,types
from pathlib import Path
from ..runtime import install_extras,fingerprint
from ..dependencies import HERE as STUDY,ROOT,sha

HERE=Path(__file__).resolve().parent

def adapted_session(lock,grant):
    from u_re.v01.experiments.action_priority_01.real_gemma_abba03 import session as proven
    ids=[t['instance_id'] for t in json.loads((HERE/'ABBA_EXPERIMENT_LOCK.json').read_bytes())['tasks']]
    code=inspect.getsource(proven.run)
    substitutions={
        "lock=json.loads((PRIOR/'ABBA_EXPERIMENT_LOCK.json').read_bytes())":"lock=V02B_LOCK",
        "grant=json.loads((HERE/'GPU_AUTHORIZATION.json').read_bytes())":"grant=V02B_GRANT",
        "assert grant['GPU_authorized'] and grant['max_SaveKernel_dispatches']==1 and grant['max_Agent_runs']==4":"assert (mode=='CPU_DRY_RUN' and not grant['GPU_authorized']) or (mode=='GPU' and grant['GPU_authorized'] and grant['max_SaveKernel_dispatches']==1 and grant['max_Agent_runs']==4)",
        "assert grant['order']==lock['order'] and grant['Agent_seconds']==300 and grant['platform_window_seconds']==10000":"assert grant['order']==lock['order'] and grant['Agent_seconds']==300 and grant['platform_window_seconds']==10000",
        "EVIDENCE_RECONCILED_TWO_TASKS_ADMITTED":"EVIDENCE_RECONCILED_FOUR_TASKS_ADMITTED",
        "['fastapi_9425','fastapi_14786']":repr(ids),
        "GPU03_PAYLOAD_END_TO_END_CPU_PASS":"V02B_PAYLOAD_END_TO_END_CPU_PASS",
    }
    for old,new in substitutions.items():
        assert old in code,('GPU03 adaptation anchor drift',old)
        code=code.replace(old,new)
    namespace=dict(proven.__dict__,HERE=HERE,ROOT=ROOT,__name__=__name__,V02B_LOCK=lock,V02B_GRANT=grant)
    exec(compile(code,'<V02b-minimal-GPU03-session-adaptation>','exec'),namespace)
    return namespace['run']

async def run(output,session_started,*,mode='GPU',cpu_transport=None,quota_at_dispatch=None,authorization=None,batch=None):
    # This guard precedes dependency installs, model allocation and inference.
    assert mode in ('CPU_DRY_RUN','GPU')
    shared=json.loads((HERE/'ABBA_EXPERIMENT_LOCK.json').read_bytes())
    grant=json.loads((HERE/'GPU_AUTHORIZATION.json').read_bytes())
    if mode=='GPU':
        assert cpu_transport is None,'Scripted transport forbidden in GPU production route'
        assert authorization and authorization.get('GPU_authorized') is True,'GPU NOT_AUTHORIZED for the new V02b environment/cohort'
        assert batch in (1,2) and authorization['experiment_id']==shared['experiment_id']
        assert authorization['environment_lock_sha256']==shared['environment_lock_sha256']
        assert authorization['frozen_order']==shared['order'] and authorization['arms']==shared['arms']
        assert authorization['model_files']==shared['model']['files']
        assert authorization['GPU']=='4xNVIDIA L4' and authorization['TP']==4 and authorization['Agent_seconds']==300
        assert authorization['max_batches']==2 and authorization['max_sessions_per_batch']==4 and authorization['platform_window_seconds']==10000
        selected=[r for r in shared['order'] if r['batch']==batch]
        shared=dict(shared,order=selected,tasks=[t for t in shared['tasks'] if t['instance_id'] in {r['instance_id'] for r in selected}])
        grant=dict(authorization,order=selected,max_SaveKernel_dispatches=1,max_Agent_runs=4,quota_at_dispatch_report_seconds=quota_at_dispatch)
    else:assert cpu_transport is not None and not grant['GPU_authorized']
    from harness_v2.evidence import atomic_json
    lock=json.loads((STUDY/'V02B_ENVIRONMENT_LOCK.json').read_bytes())
    actual=install_extras(Path(output).parent/'environment')
    assert actual==lock['fingerprint'],'Production environment differs from screened environment'
    atomic_json(Path(output).parent/'PRODUCTION_ENVIRONMENT_BEFORE.json',actual)
    await adapted_session(shared,grant)(output,session_started,mode=mode,cpu_transport=cpu_transport,quota_at_dispatch=quota_at_dispatch)
    assert fingerprint()==actual,'Production run changed frozen trusted dependency environment'
    atomic_json(Path(output).parent/'PRODUCTION_ENVIRONMENT_AFTER.json',fingerprint())
