"""Offline observation only. No decisions or stop callbacks affect the Agent."""
import hashlib
import json
from pathlib import Path


def inspect_case(directory):
    root=Path(directory)
    requests=[json.loads(line) for line in (root/'request_snapshots.jsonl').read_text().splitlines()]
    from harness_v2.evidence import read_events
    from .runner_cases import tool_events
    events=tool_events(read_events(root/'adk_events.jsonl'))
    responses={e['id']:e for e in events if e['kind']=='function_response'}
    seen=set();observations=[]
    for e in events:
        if e['kind']!='function_call' or not e['id'].startswith('ure_'):
            continue
        index=int(e['id'].split('_')[1])-1
        source=requests[index]['files'].get('app.py')
        response=responses.get(e['id'],{}).get('result') or {}
        action=dict(tool=e['tool'],args=e['args'],source_sha256=source,response=response)
        if e['tool']=='run_command':
            key=(source,e['args']['command'])
            action['progress']='NO_INCREMENTAL_PROGRESS' if key in seen else 'NEW_EVIDENCE'
            seen.add(key)
            action['scope']='Controlled toy environment is unchanged; this signature is not a general semantic-equivalence classifier.'
        elif e['tool']=='edit_file':
            action['progress']='CANDIDATE_EDIT_PENDING_CHECK'
        else:
            action['progress']='NOT_A_BEHAVIOR_CHECK'
        observations.append(action)
    return dict(observations=observations,unchanged_command_repetitions=sum(e['progress']=='NO_INCREMENTAL_PROGRESS' for e in observations),
        online_enforcement=False,scripted_model=True,
        warning='A first failing assertion/no-match search is NEW_EVIDENCE. Repetition may be justified by unobserved environment/hypothesis/confidence changes in real tasks; manually audit those before labeling waste.')
