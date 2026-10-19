"""Post-supervisor evidence gate; no GPU launcher or scoring changes."""
import json
from pathlib import Path
from harness_v2.evidence import read_events
from s1.audit import inspect_run as r04_audit
from .wire import audit_requests


def deadline_proof(directory):
    d=Path(directory)
    def load(name):
        p=d/name
        return json.loads(p.read_text()) if p.exists() else {}
    raw=load('official_result.json');boundary=load('agent_boundary.json')
    controller=load('audit_result.json');done=load('worker_done.json')
    runtime=load('runtime_config.json')
    seconds=runtime.get('budget',{}).get('agent_seconds')
    elapsed=load('progress.json').get('agent_elapsed_seconds')
    error=raw.get('error_message') or boundary.get('agent_error') or ''
    endings=[e for e in read_events(d/'events.jsonl') if e.get('stage')=='save_patch' and 'agent_elapsed_seconds' in e]
    budget_match=isinstance(seconds,(int,float)) and isinstance(elapsed,(int,float)) and seconds-1<=elapsed<=seconds+5
    return dict(official_agent_deadline=error.startswith('Agent exceeded session timeout (') and budget_match and bool(endings),
        cleanup_verified=bool(controller.get('process_tree_stopped') and controller.get('cleanup_complete') and done.get('cleanup_complete')),
        official_error=error,registered_agent_seconds=seconds,observed_agent_seconds=elapsed,
        cutoff_monotonic=endings[-1]['recorded_monotonic'] if endings else None)


def inspect_run(directory,config,model_path):
    result=r04_audit(directory,config,model_path)
    proof=deadline_proof(directory)
    lifecycle=audit_requests(directory,deadline_evidence=proof)
    # Remove only the old unmatched-count finding when the stronger ID-based
    # gate has independently explained every request. Other checks still stand.
    if lifecycle['passed']:
        result['reasons']=[r for r in result['reasons'] if r!='missing/unmatched HTTP']
    else:result['reasons']+=['http_lifecycle:'+r for r in lifecycle['reasons']]
    phase2=result.get('phase2') or {}
    output=phase2.get('stdout','')+'\n'+phase2.get('stderr','')
    if 'recursive dependency involving fixture' in output:
        result['outcome']=dict(status='unknown',failure_stage='verifier_environment',
            reason='fixture_provider_missing_or_unregistered; test setup is not an attributable repair verdict')
        result['reasons'].append('verifier_fixture_environment')
    result['http_lifecycle']=lifecycle;result['deadline_proof']=proof
    result['usage']=lifecycle['observed_response_usage']
    result['usage_complete']=lifecycle['usage_complete']
    result['partial_token_usage']=lifecycle['partial_token_usage']
    result['usage_scope']=lifecycle['scope']
    result['reasons']=sorted(set(result['reasons']))
    result['infrastructure_passed']=not result['reasons']
    return result
