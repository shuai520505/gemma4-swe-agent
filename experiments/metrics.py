"""Conservative metrics; missing/incomplete runs never become passing scores."""
import re
from statistics import mean


def classify(result, output, patch):
    invoked = output.startswith('STDOUT:\n') and '\nSTDERR:\n' in output
    collection = invoked and bool(re.search(r'ERROR collecting|errors? during collection', output, re.I))
    # This is an application-validity metric, not a semantic correctness claim.
    valid = bool(patch and invoked and 'Failed to apply agent patch' not in output)
    return dict(phase2_invoked=invoked, collection_failed=collection,
                patch_application_valid=valid,
                test_bodies_observed=bool(invoked and re.search(r'\b\d+ (?:passed|failed)\b', output)),
                verifier_timeout=result.get('test_exit_code') == 124)


def summarize(records, schedule):
    output = {'planned_runs': len(schedule), 'observed_runs': len(records),
              'complete': len(records) == len(schedule), 'competition_score': None, 'arms': {}}
    for arm in ('v0', 'v1'):
        planned = [r for r in schedule if r['arm'] == arm]
        actual = [r for r in records if r['arm'] == arm]
        invoked = [r for r in actual if r.get('phase2_invoked')]
        observed = [r for r in actual if r.get('duration_seconds') is not None]
        n = len(planned)
        output['arms'][arm] = dict(planned=n, observed=len(actual),
            resolved=sum(r.get('resolved') is True for r in actual),
            resolution_rate=sum(r.get('resolved') is True for r in actual) / n if n and len(actual) == n else None,
            patch_validity_rate=sum(r.get('patch_application_valid') is True for r in actual) / n if n and len(actual) == n else None,
            collection_failure_rate_all_planned=sum(r.get('collection_failed') is True for r in actual) / n if n and len(actual) == n else None,
            collection_failure_rate_invoked=sum(r.get('collection_failed') is True for r in invoked) / len(invoked) if invoked else None,
            phase2_invoked=len(invoked), timeouts=sum(r.get('outer_timeout') is True or r.get('verifier_timeout') is True or r.get('agent_timeout') is True for r in actual),
            errors=sum(bool(r.get('execution_error')) for r in actual),
            mean_llm_calls=mean(r['total_llm_calls'] for r in actual if r.get('total_llm_calls') is not None) if any(r.get('total_llm_calls') is not None for r in actual) else None,
            mean_tool_calls=mean(r['tool_calls'] for r in actual if r.get('tool_calls') is not None) if any(r.get('tool_calls') is not None for r in actual) else None,
            mean_duration_seconds=mean(r['duration_seconds'] for r in observed) if observed else None)
    pairs = {}
    for row in records:
        pairs.setdefault(row['instance_id'], {})[row['arm']] = row
    paired = [v for v in pairs.values() if set(v) == {'v0', 'v1'}]
    output['paired'] = dict(n=len(paired),
        v1_only_resolved=sum(p['v1'].get('resolved') is True and p['v0'].get('resolved') is not True for p in paired),
        v0_only_resolved=sum(p['v0'].get('resolved') is True and p['v1'].get('resolved') is not True for p in paired))
    return output
