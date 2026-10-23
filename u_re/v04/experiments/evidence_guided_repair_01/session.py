"""Reuse sealed official/chroot coordinator; only select the two candidate paths."""
import inspect,json
from pathlib import Path
from .common import HERE,ROOT,PACKAGE
from u_re.v02.experiments.env_recovery_admission_01.runtime import install_extras,fingerprint
def coordinator(lock,grant):
    from u_re.v03.experiments.context_budget_01 import session as prior
    code=inspect.getsource(prior.coordinator)
    old='"agent=ROOT/\'u_re/v01/experiments/action_priority_01/candidate_action_v01\'"'
    new='"agent=ROOT/\'u_re/v01/experiments/action_priority_01/candidate_action_v01\' if arm==\'A\' else ROOT/\'u_re/v04/experiments/evidence_guided_repair_01/candidate_egr_v04\'"'
    assert code.count(old)==1
    code=code.replace(old,new).replace('V03_PAYLOAD_END_TO_END_CPU_PASS','V04_EGR_PAYLOAD_END_TO_END_CPU_PASS').replace('V03_CONTEXT_PILOT_COMPLETE','V04_EGR_GPU_NOT_AUTHORIZED')
    namespace=dict(prior.__dict__,HERE=HERE,ROOT=ROOT,__name__=__name__,__package__=PACKAGE)
    exec(compile(code,'<Reused-V03-coordinator-two-frozen-Prompts>','exec'),namespace)
    return namespace['coordinator'](lock,grant)

async def run(output,session_started,*,mode='CPU_DRY_RUN',cpu_transport=None,**kwargs):
    # No current GPU authorization; no dependency installation or model load
    # precedes this gate. The candidate ZIP itself is standard official format.
    assert mode=='CPU_DRY_RUN' and cpu_transport is not None,'V04 GPU NOT_AUTHORIZED'
    from harness_v2.evidence import atomic_json
    lock=json.loads((HERE/'ABBA_EXPERIMENT_LOCK.json').read_bytes())
    grant=dict(GPU_authorized=False,order=lock['order'],Agent_seconds=300,platform_window_seconds=10000)
    env=json.loads((ROOT/'u_re/v02/experiments/env_recovery_admission_01/V02B_ENVIRONMENT_LOCK.json').read_bytes())
    before=install_extras(Path(output).parent/'environment');assert before==env['fingerprint']
    atomic_json(Path(output).parent/'PRODUCTION_ENVIRONMENT_BEFORE.json',before)
    await coordinator(lock,grant)(output,session_started,mode=mode,cpu_transport=cpu_transport)
    assert fingerprint()==before
    atomic_json(Path(output).parent/'PRODUCTION_ENVIRONMENT_AFTER.json',fingerprint())
