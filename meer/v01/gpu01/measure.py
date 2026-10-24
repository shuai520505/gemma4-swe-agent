"""Private, post-run observation only; never imported by the Agent/worker.

Do not infer Issue relevance, semantic correctness, or model intent from a local
check. Absence of a complete trace is UNKNOWN, not a zero invocation count.
"""
import hashlib
import json
from pathlib import Path


def lines(path):
    path=Path(path)
    return [json.loads(x) for x in path.read_bytes().splitlines() if x.strip()] if path.exists() else None


def observe(directory):
    directory=Path(directory)
    events=lines(directory/'agent/adk_events.jsonl')
    if events is None:
        return dict(status='NOT_RUN_OR_MISSING_TRACE',native_resolved=None,
                    Skill_invocations=None,mechanism_bypassed=None,model_requests=None,
                    prompt_tokens=None,completion_tokens=None,total_tokens=None)
    responses=[]; calls=[]; usage=[]
    for row in events:
        event=row.get('event',{})
        if event.get('usage_metadata'):usage.append(event['usage_metadata'])
        for part in event.get('content',{}).get('parts',[]):
            if part.get('function_call'):calls.append(dict(time=row.get('recorded_monotonic'),**part['function_call']))
            if part.get('function_response'):responses.append(dict(time=row.get('recorded_monotonic'),**part['function_response']))
    verifier=[]
    for row in responses:
        if row['name']!='run_skill_script':continue
        response=row.get('response',{})
        if isinstance(response,dict) and isinstance(response.get('stdout'),str):
            try:
                value=json.loads(response['stdout'])
                if value.get('schema') in ('MEER_EVIDENCE_V1','MEER_PROMPT_ONLY_CONTROL'):
                    verifier.append(dict(time=row['time'],**value))
            except (ValueError,AttributeError):pass
    names=[r['name'] for r in calls]
    agent_path=directory/'agent/agent_result.json'
    agent=json.loads(agent_path.read_bytes()) if agent_path.exists() else {}
    result_path=directory/'official_result.json'
    result=json.loads(result_path.read_bytes()) if result_path.exists() else {}
    complete=(directory/'worker_done.json').exists()
    def total(key):
        return sum(v[key] for v in usage) if usage and all(v.get(key) is not None for v in usage) else None
    wire=lines(directory/'agent/http_wire.jsonl')
    # Avoid double counting HTTP retries/tool-event usage. Both raw sources are
    # preserved; usage below is the actual ADK received usage, not estimates.
    submits=[i for i,n in enumerate(names) if n=='submit_patch']
    source=[]
    for path in (directory/'agent').rglob('events.jsonl'):
        for row in lines(path) or []:
            if row.get('kind')=='source_boundary_observation' and row.get('production_changed'):
                source.append(row)
    patch=directory/'final.patch'
    return dict(status='OBSERVED',trace_complete=complete,native_resolved=result.get('resolved'),
        official_patch_submitted=agent.get('patch_submitted'),
        final_patch_sha256=hashlib.sha256(patch.read_bytes()).hexdigest() if patch.exists() else None,
        Skill_discovery_calls=names.count('list_skills'),Skill_load_calls=names.count('load_skill'),
        Skill_invocations=names.count('run_skill_script'),recognized_verifier_results=len(verifier),
        verifier_events=verifier,
        mechanism_bypassed=(names.count('run_skill_script')==0) if complete else None,
        applicability_of_mechanism_bypass='Requires task/arm review; A has no Skill',
        executed_assertions=sum(v['executed_assertions'] for v in verifier if isinstance(v.get('executed_assertions'),int)) if verifier else None,
        first_production_change_observation_monotonic=min((r['end_monotonic'] for r in source),default=None),
        first_relevant_behavior_edit_seconds=None,meaningful_regression_test=None,
        final_patch_tested_after_last_edit=None,acted_on_evidence=None,unverified_success_claims=None,
        human_review_required='Relevance, claim semantics, evidence-to-action causality and meaningful test coverage',
        post_submit_tool_calls=len(names)-submits[0]-1 if submits else None,
        submit_call_count=len(submits),successful_submit_count=None,
        charged_tools=agent.get('charged_tools'),agent_wall_seconds=agent.get('agent_seconds'),
        model_requests=sum(r.get('kind')=='http_request' for r in wire) if wire is not None else None,
        prompt_tokens=total('prompt_token_count'),completion_tokens=total('candidates_token_count'),
        total_tokens=total('total_token_count'),received_thinking_tokens=total('thoughts_token_count'),
        usage_source='Actual received ADK usage_metadata; missing component remains null')
