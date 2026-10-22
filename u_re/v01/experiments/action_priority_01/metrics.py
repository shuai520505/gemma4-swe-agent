"""Offline evidence reduction only. Never imported by an Agent or CPU worker.

Input is a versioned, research-side projection with raw event IDs/hashes. A raw
tool call alone cannot certify a source edit or a valid patch. Missing evidence
keeps a metric null; this module never executes tests or repairs code.
"""
import json
import re
from pathlib import Path

SHA = re.compile(r'[a-f0-9]{64}')


def backed(event):
    return bool(event.get('raw_event_id') and SHA.fullmatch(event.get('raw_artifact_sha256','')))


def summarize(run):
    assert run['schema_version'] == 1
    events = run.get('events')
    if events is None:
        return dict(status=run['status'],resolved=run.get('native_resolved'),event_metrics=None)
    assert all(e['seconds'] >= 0 for e in events)
    assert [e['seconds'] for e in events] == sorted(e['seconds'] for e in events)
    # Evidence-referenced records only; unbacked rows are reported, never promoted.
    rows = [e for e in events if backed(e)]
    edits = [e for e in rows if e['kind']=='file_change' and e.get('path_class')=='production'
             and e.get('before_sha256') != e.get('after_sha256')
             and SHA.fullmatch(e.get('before_sha256','')) and SHA.fullmatch(e.get('after_sha256',''))]
    patches = [e for e in rows if e['kind']=='patch' and e.get('bytes',0)>0
               and e.get('applies_cleanly') is True and e.get('diff_check_exit')==0
               and e.get('production_paths') and SHA.fullmatch(e.get('patch_sha256',''))]
    supported = []
    required = set(run.get('registered_target_check_ids',[]))
    for p in patches:
        if not SHA.fullmatch(p.get('source_tree_sha256','')): continue
        checks = [e for e in rows if e['kind']=='check' and e.get('seconds',0)>=p['seconds']
                  and e.get('patch_sha256')==p['patch_sha256']
                  and e.get('source_tree_sha256')==p.get('source_tree_sha256')
                  and e.get('workspace_source_proven') is True and e.get('assertions_executed') is True
                  and e.get('exit_code')==0]
        if required and required <= {e.get('check_id') for e in checks}:
            # End of the last required check, not backdated to the edit's time.
            supported.append(max(min(e['seconds'] for e in checks if e.get('check_id')==i) for i in required))
    submit = [e for e in rows if e['kind']=='tool_response' and e.get('name')=='submit_patch' and e.get('status')=='ok']
    first = submit[0]['seconds'] if submit else None
    after = [e for e in rows[rows.index(submit[0])+1:] if e['kind']=='tool_call'] if submit else []
    repeated = dict(search=0,test=0); seen = set()
    for e in rows:
        if e['kind']!='operation' or e.get('operation_class') not in repeated: continue
        fields=('command_sha256','source_tree_sha256','input_sha256','environment_sha256','result_sha256')
        if not all(SHA.fullmatch(e.get(k,'')) for k in fields): continue
        key=(e['operation_class'],*(e[k] for k in fields))
        if key in seen: repeated[e['operation_class']]+=1
        seen.add(key)
    requests = [e for e in rows if e['kind']=='model_request']
    usage = [e.get('usage') for e in requests]
    capture_complete = run.get('model_request_capture_complete') is True
    def valid(u):
        return isinstance(u,dict) and all(type(u.get(k)) is int for k in ('prompt_tokens','completion_tokens'))
    complete = capture_complete and all(valid(u) for u in usage)
    prompt_values = [u['prompt_tokens'] for u in usage if isinstance(u,dict) and type(u.get('prompt_tokens')) is int]
    completion_values = [u['completion_tokens'] for u in usage if isinstance(u,dict) and type(u.get('completion_tokens')) is int]
    known_prompt, known_completion = sum(prompt_values), sum(completion_values)
    charged = [e.get('charged_tool_count') for e in rows if e['kind']=='official_budget']
    final = run.get('final_patch_bytes')
    return dict(status=run['status'],resolved=run.get('native_resolved'),
        time_to_first_source_edit=edits[0]['seconds'] if edits else None,
        time_to_first_applicable_patch=patches[0]['seconds'] if patches else None,
        time_to_first_locally_supported_patch=min(supported) if supported else None,
        final_nonempty_patch=None if final is None else final>0,
        successful_submit=bool(submit),successful_submits=len(submit),post_submit_tool_calls=len(after),
        identical_successful_resubmits=sum(bool(SHA.fullmatch(e.get('patch_sha256',''))) and any(
            e.get('patch_sha256')==earlier.get('patch_sha256') for earlier in submit[:i])
            for i,e in enumerate(submit)),
        first_successful_submit_seconds=first,
        post_submit_seconds=None if first is None or run.get('agent_wall_seconds') is None
            else run['agent_wall_seconds']-first,
        repeated_search_candidates=repeated['search'],repeated_unchanged_test_candidates=repeated['test'],
        charged_tools=charged[-1] if charged else None,
        total_model_requests=len(requests) if capture_complete else None,
        observed_model_requests=len(requests),model_request_capture_complete=capture_complete,
        usage_complete=complete,prompt_tokens=known_prompt if complete else None,
        completion_tokens=known_completion if complete else None,
        received_prompt_tokens_partial=known_prompt if prompt_values else None,
        received_completion_tokens_partial=known_completion if completion_values else None,
        missing_usage_requests=sum(not valid(u) for u in usage),
        agent_wall_seconds=run.get('agent_wall_seconds'),worker_wall_seconds=run.get('worker_wall_seconds'),
        unbacked_events=len(events)-len(rows),
        caveat='Locally supported != native resolved. Exact repetition is a review candidate, not proof of wasted work.')


if __name__=='__main__':
    import sys
    print(json.dumps(summarize(json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))),indent=2))
