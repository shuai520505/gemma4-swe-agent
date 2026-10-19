"""The same file-based verifier path is used by replay, native CPU and GPU workers."""
import hashlib
import json
from pathlib import Path
import re
from harness_v2.evidence import read_events
from s1.audit import inspect_run as legacy_audit
from s1.infrastructure_recovery.session import deadline_proof
from s1.infrastructure_recovery.wire import audit_requests
from .classification import classify,blocked


def load(directory,name,default=None):
    file=Path(directory)/name
    return json.loads(file.read_text()) if file.is_file() else default


def audit_verifier(directory,*,baseline=None,historical_attestation=None):
    directory=Path(directory);execution=load(directory,'phase2_execution.json')
    legacy=historical_attestation is not None
    if legacy:
        actual=hashlib.sha256((directory/'phase2_execution.json').read_bytes()).hexdigest()
        if actual!=historical_attestation['phase2_sha256']:
            return blocked('unknown_unparsed','Frozen historical execution hash mismatch')
    metadata=load(directory,'phase2_junit_capture.json',{})
    raw=(directory/'phase2.junit.xml').read_bytes() if (directory/'phase2.junit.xml').is_file() else None
    if not legacy:
        if metadata.get('status')!='captured' or raw is None:
            return classify(execution,None,baseline=baseline)
        if hashlib.sha256(raw).hexdigest()!=metadata.get('sha256'):
            return blocked('unknown_unparsed','Original JUnit byte hash mismatch')
        if not metadata.get('sandbox_exists_at_capture'):
            return blocked('unknown_unparsed','JUnit capture timing not proven')
    result=classify(execution,raw,baseline=baseline,historical_legacy=legacy)
    # Direct parser failures can be attributed conservatively to a changed
    # production file, using error-node traceback + baseline/current SHA. A
    # generic import/setup exception is deliberately NOT called environmental.
    if result.get('infrastructure_stop') and baseline and baseline.get('eligible') and metadata:
        previous=baseline.get('production_source_hashes',{})
        current=metadata.get('production_source_hashes',{})
        workspace=Path(metadata.get('workspace_realpath','/nonexistent'))
        for event in result.get('events',[]):
            if event.get('category') not in ('setup_error','collection_error'):continue
            details=event.get('details','')
            kind=re.search(r'(?:^|\n)(?:E\s+)?\s*(SyntaxError|IndentationError|TabError):',details)
            files=re.findall(r'(?:^|\n)(?:E\s+)?\s*File "([^"]+)", line \d+',details)
            if not kind or not files:continue
            try:name=Path(files[-1]).resolve().relative_to(workspace.resolve()).as_posix()
            except ValueError:continue
            if name in previous and name in current and previous[name]!=current[name]:
                result.update(attribution='agent_regression',infrastructure_stop=False,confirmed_failure=True,
                    causal_evidence=dict(exception=kind[1],root_file=name,baseline_sha256=previous[name],
                        executed_sha256=current[name],basis='Real JUnit error traceback and changed production bytes'))
    return result


def inspect_run(directory,config,model_path,*,baseline):
    result=legacy_audit(directory,config,model_path)
    proof=deadline_proof(directory);http=audit_requests(directory,deadline_evidence=proof)
    structured=audit_verifier(directory,baseline=baseline)
    reasons=list(result['reasons'])
    if http['passed']:reasons=[r for r in reasons if r!='missing/unmatched HTTP']
    else:reasons+=['http_lifecycle:'+r for r in http['reasons']]
    if not structured['infrastructure_stop']:
        # These legacy findings derive from text-based outcome normalization or
        # empty Patch policy. Native structured evidence supersedes only those.
        reasons=[r for r in reasons if r not in ('unconfirmed repair verdict','empty Patch; no complete infrastructure gate')]
        raw=load(directory,'official_result.json',{})
        failed=structured.get('confirmed_failure',False)
        if (failed and raw.get('resolved') is True) or (not failed and raw.get('resolved') is not True):
            reasons.append('native_verdict_structured_evidence_contradiction')
            result['outcome']=dict(status='unknown',failure_stage='verification_integrity')
        else:result['outcome']=dict(status='failed' if failed else 'resolved',failure_stage='verification' if failed else None,
            reason=structured['category'])
    else:
        reasons.append('structured_verifier:'+structured['category']+':'+structured['reason'])
        result['outcome']=dict(status='unknown',failure_stage='verification_attribution',reason=structured['reason'])
    result.update(structured_verifier=structured,http_lifecycle=http,deadline_proof=proof,
        usage=http['observed_response_usage'],usage_complete=http['usage_complete'],partial_token_usage=http['partial_token_usage'],
        usage_scope=http['scope'],reasons=sorted(set(reasons)),infrastructure_passed=not reasons)
    return result
