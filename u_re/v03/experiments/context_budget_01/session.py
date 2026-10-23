"""Reuse actual GPU03 production coordinator with only registered cap adaptation."""
import inspect,json,time
from pathlib import Path
from .common import HERE,ROOT,ID,sha
from .policy import boundary_checks
from u_re.v02.experiments.env_recovery_admission_01.runtime import install_extras,fingerprint

def coordinator(lock,grant):
    from u_re.v01.experiments.action_priority_01.real_gemma_abba03 import session as proven
    code=inspect.getsource(proven.run)
    changes={
        'from ..integrated_cpu_01.agent_phase import SubprocessManager':'from u_re.v01.experiments.action_priority_01.integrated_cpu_01.agent_phase import SubprocessManager',
        'from .ISOLATION_CANARY import CANARY':'from u_re.v01.experiments.action_priority_01.real_gemma_abba03.ISOLATION_CANARY import CANARY',
        "lock=json.loads((PRIOR/'ABBA_EXPERIMENT_LOCK.json').read_bytes())":"lock=LOCK",
        "grant=json.loads((HERE/'GPU_AUTHORIZATION.json').read_bytes())":"grant=GRANT",
        "assert grant['GPU_authorized'] and grant['max_SaveKernel_dispatches']==1 and grant['max_Agent_runs']==4":"assert (mode=='CPU_DRY_RUN' and not grant['GPU_authorized']) or (mode=='GPU' and grant['GPU_authorized'] and grant['max_SaveKernel_dispatches']==1 and grant['max_Agent_runs']==4)",
        "['fastapi_9425','fastapi_14786']":"['fastapi_5077','fastapi_11355']",
        "[dict(run=1,instance_id='ure_gpu03_owned',arm='A')]":"[dict(run=1,instance_id='ure_gpu03_owned',arm='A'),dict(run=2,instance_id='ure_gpu03_owned',arm='B')]",
        "agent=ROOT/'u_re/v01/candidate_noegv' if arm=='A' else ROOT/'u_re/v01/experiments/action_priority_01/candidate_action_v01'":"agent=ROOT/'u_re/v01/experiments/action_priority_01/candidate_action_v01'",
        "model_transport='REAL_GEMMA' if mode=='GPU' else 'CPU_SCRIPTED_ONLY')":"model_transport='REAL_GEMMA' if mode=='GPU' else 'CPU_SCRIPTED_ONLY',candidate_sha256=lock['arms'][arm]['ZIP_sha256'])",
        'GPU03_PAYLOAD_END_TO_END_CPU_PASS':'V03_PAYLOAD_END_TO_END_CPU_PASS',
        'GPU03_REAL_GEMMA_ABBA_COMPLETE':'V03_CONTEXT_PILOT_COMPLETE',
        'owned_scripted_runs=1':'owned_scripted_runs=2',
    }
    for old,new in changes.items():
        assert old in code,('Adaptation source drift',old)
        code=code.replace(old,new)
    namespace=dict(proven.__dict__,HERE=HERE,ROOT=ROOT,__name__=__name__,__package__=__package__,LOCK=lock,GRANT=grant)
    exec(compile(code,'<Reused-GPU03-V03-context-coordinator>','exec'),namespace)
    return namespace['run']

async def run(output,session_started,*,mode='GPU',cpu_transport=None,quota_at_dispatch=None,authorization=None):
    from harness_v2.evidence import atomic_json
    lock=json.loads((HERE/'ABBA_EXPERIMENT_LOCK.json').read_bytes())
    assert mode in ('GPU','CPU_DRY_RUN')
    if mode=='GPU':
        assert cpu_transport is None and authorization and authorization['GPU_authorized']
        assert authorization['experiment_id']==ID and authorization['order']==lock['order']
        assert authorization['policy_freeze_sha256']==sha((HERE/'CONTEXT_POLICY_FREEZE.json').read_bytes())
        assert authorization['max_SaveKernel_dispatches']==1 and authorization['max_Agent_runs']==4
        grant=dict(authorization,quota_at_dispatch_report_seconds=quota_at_dispatch)
    else:
        assert cpu_transport is not None
        grant=dict(GPU_authorized=False,order=lock['order'],Agent_seconds=300,platform_window_seconds=10000)
    env=json.loads((ROOT/'u_re/v02/experiments/env_recovery_admission_01/V02B_ENVIRONMENT_LOCK.json').read_bytes())
    before=install_extras(Path(output).parent/'environment');assert before==env['fingerprint']
    atomic_json(Path(output).parent/'PRODUCTION_ENVIRONMENT_BEFORE.json',before)
    atomic_json(Path(output).parent/'POLICY_BOUNDARY_CHECKS.json',await boundary_checks())
    await coordinator(lock,grant)(output,session_started,mode=mode,cpu_transport=cpu_transport,quota_at_dispatch=quota_at_dispatch)
    assert fingerprint()==before
    atomic_json(Path(output).parent/'PRODUCTION_ENVIRONMENT_AFTER.json',fingerprint())
