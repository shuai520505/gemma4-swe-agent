"""Reuse PR43 coordinator; bind new immutable inputs and native endpoint stop rule."""
import asyncio,json,sys
from pathlib import Path
from unittest.mock import patch
from r2a_runtime import HERE,write

def admission(row,outcome):
    if not outcome.get('allow_next_run') or not row.get('cleanup'):return 'STOP'
    error=str(row.get('agent_error') or '').lower()
    if any(x in error for x in ('context','backend','connection','server error','out of memory','internalservererror')):return 'STOP'
    native=row['evaluation']['sdk_native']
    if native['test_exit_code'] not in (0,1):return 'STOP'
    observed=native.get('observed_junit',{})
    if not observed or observed.get('errors') or not observed.get('positive_controls_passed'):return 'STOP'
    if native.get('error') and native['test_exit_code']==0:return 'STOP'
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
    def supervise(*args,**kwargs):
        # Official independent verification allows 300s plus fresh sandbox setup.
        # This host cap is separate from the unchanged 240s Agent command limit.
        caps=dict(kwargs.get('stage_caps') or {});caps['verification']=600;kwargs['stage_caps']=caps
        return original_supervise(*args,**kwargs)
    with patch.object(r12_final_cpu,'admission',admission),patch.object(supervision,'supervise',supervise):
        await prior.run(out,float(started),execution)
    write(Path(out)/'ENDPOINT_SCOPE.json',dict(endpoint='Official SDK resolved on selected public SWE-bench tasks',hidden_competition_native_resolved=None,canonical_SWEbench_resolved=None,semantic_review='REQUIRED_SEPARATELY',legacy_coordinator_scope_flags='Historical generic coordinator fields do not describe this endpoint; use each sdk_native record.'))

if __name__=='__main__':asyncio.run(run(sys.argv[1],sys.argv[2]))
