"""Reuse PR43 coordinator; bind new immutable inputs and native endpoint stop rule."""
import asyncio,json,sys,time
from pathlib import Path
from unittest.mock import patch
from r2a_runtime import HERE,write

def admission(row,outcome):
    if not outcome.get('allow_next_run') or not row.get('cleanup') or not row.get('evidence_complete'):return 'STOP'
    error=str(row.get('agent_error') or '').lower()
    if any(x in error for x in ('context','backend','connection','server error','out of memory','internalservererror')):return 'STOP'
    native=row['evaluation']['sdk_native']
    if str(native.get('error') or '').startswith('Failed to apply agent patch:'):return 'CONTINUE'
    if native['test_exit_code'] not in (0,1):return 'STOP'
    observed=native.get('observed_junit',{})
    controls=(native.get('infrastructure_controls') or {}).get('passed',observed.get('positive_controls_passed'))
    if not observed or observed.get('errors') or not controls:return 'STOP'
    if not (native.get('verification_source_guard') or {}).get('unchanged'):return 'STOP'
    if native.get('error') and native['test_exit_code']==0:
        known_matcher=str(native['error']).startswith('Required test node did not pass:')
        exact=native.get('independent_exact',{}).get('status')=='INDEPENDENT_TEST_PASS'
        if not (known_matcher and exact):return 'STOP'
    return 'CONTINUE'

async def run(out,started):
    import gemma_pair.coordinator as prior
    import r12_final_cpu
    import harness_v2.supervisor as supervision
    plan=json.loads((HERE/'EXECUTION_PLAN.json').read_bytes())
    issues=json.loads((HERE/'ISSUES.agent.json').read_bytes());identity=json.loads((HERE/'TASK_IDENTITY_LOCK.json').read_bytes())['rows']
    bindings={r['instance_id']:dict(issue=r,snapshot=str(HERE/'assets/snapshots'/(r['instance_id']+'.tgz')),wheels=str(HERE/'assets/wheels'),version=next(t['version'] for t in identity if t['instance_id']==r['instance_id'])) for r in issues}
    execution=dict(bindings=bindings,order=[(r['task'],r['candidate']) for r in plan['sessions']],window_seconds=18000,new_explicit_GPU_authorization=True,worker_module='r2a_worker')
    # Host-side admission only, identically applied to both arms; no Agent policy change.
    original_supervise=supervision.supervise
    admitted_workers=0
    def supervise(*args,**kwargs):
        nonlocal admitted_workers
        # Official independent verification allows 300s plus fresh sandbox setup.
        # This host cap is separate from the unchanged 240s Agent command limit.
        caps=dict(kwargs.get('stage_caps') or {});caps['verification']=600;kwargs['stage_caps']=caps
        # Host preparation, Agent deadline+grace, native setup/verification and
        # cleanup all need room. This changes no Agent/model/tool budget.
        remaining=len(plan['sessions'])-admitted_workers
        assert 18000-(time.monotonic()-float(started))>=1680*remaining+900,'Insufficient full host-stage reserve'
        kwargs['outer_seconds']=1680;admitted_workers+=1
        return original_supervise(*args,**kwargs)
    with patch.object(r12_final_cpu,'admission',admission),patch.object(supervision,'supervise',supervise):
        await prior.run(out,float(started),execution)
    write(Path(out)/'ENDPOINT_SCOPE.json',dict(endpoint='User-approved independent exact tests plus effective production fix and semantic review; raw official SDK verdict retained',hidden_competition_native_resolved=None,canonical_SWEbench_resolved=None,semantic_review='REQUIRED_SEPARATELY',legacy_coordinator_scope_flags='Historical generic coordinator fields do not describe this endpoint; use each sdk_native and independent_exact record.'))

if __name__=='__main__':asyncio.run(run(sys.argv[1],sys.argv[2]))
