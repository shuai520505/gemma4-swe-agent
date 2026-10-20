"""Verify raw evidence and export descriptive timelines; never infer mechanism from prose."""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import zipfile
from harness_v2.evidence import read_events
from s1.collect import verify_zip
from s2.egv_agenttool_t500_early_v01.analyze_pairs import summarize

HERE = Path(__file__).resolve().parent


def emit(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as handle:
        handle.write(json.dumps(obj, indent=2, ensure_ascii=False) + '\n')


def read(path, default=None):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default


def inspect_run(folder, row):
    official = read(folder / 'official_result.json', {})
    audit = read(folder / 'research_audit.json', {})
    events = read_events(folder / 'events.jsonl')
    nested = read_events(folder / 'nested_audit.jsonl')
    life = read_events(folder / 'http_lifecycle.jsonl')
    boundaries = [r['recorded_monotonic'] for r in events if r.get('kind') == 'stage' and r.get('agent_started') is True]
    t0 = boundaries[0] if boundaries else None
    seconds = lambda r: r.get('monotonic', r.get('recorded_monotonic', 0)) - t0 if t0 is not None else None
    starts = {}
    tool_rows = []
    for index, event in enumerate(nested, 1):
        key = (event.get('actor'), event.get('call_id'))
        if event['kind'] == 'tool_start':
            starts[key] = (index, event)
        if event['kind'] != 'tool_end':
            continue
        before_index, before = starts.pop(key, (None, {}))
        pre, post = before.get('files', {}), event.get('files', {})
        changed = sorted(name for name in set(pre) | set(post) if pre.get(name) != post.get(name))
        package = 'rich/' if row['instance_id'].startswith('rich_') else 'fastapi/'
        production = [name for name in changed if name.startswith(package) and name.endswith('.py')]
        result = event.get('result')
        tool_rows.append(dict(actor=event['actor'], tool=event['tool'], call_id=event['call_id'],
            start_seconds=seconds(before) if before else None, end_seconds=seconds(event),
            start_line=before_index, end_line=index, counted_tools=event.get('counted_tools'),
            arguments=event.get('args'), result=result, changed_files=changed,
            production_candidate_changes=production,
            provenance='nested_audit.jsonl',
            limitation='Production-file delta is an edit candidate, not proof of a correct or issue-relevant repair.'))
    output = folder / 'posthoc'
    emit(output / 'tool_events.json', tool_rows)
    with (output / 'tool_events.csv').open('x', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=['actor','tool','call_id','start_seconds','end_seconds',
            'start_line','end_line','counted_tools','arguments','changed_files','production_candidate_changes'])
        writer.writeheader()
        for event in tool_rows:
            writer.writerow({key: json.dumps(event[key], ensure_ascii=False) if isinstance(event[key], (dict,list)) else event[key]
                             for key in writer.fieldnames})
    terminal = [r for r in life if r.get('kind') == 'terminal_status']
    received = [r['usage'] for r in terminal if isinstance(r.get('usage'), dict)]
    sum_known = lambda rows, key: sum(r[key] for r in rows if type(r.get(key)) is int) if any(type(r.get(key)) is int for r in rows) else None
    role_usage = {}
    for role in sorted({r['actor'] for r in nested if r.get('kind') == 'model_start'}):
        ended = [r for r in nested if r.get('kind') == 'model_end' and r.get('actor') == role]
        usage = [r['usage'] for r in ended if isinstance(r.get('usage'), dict)]
        role_usage[role] = dict(model_starts=sum(r['kind']=='model_start' and r.get('actor')==role for r in nested),
            model_ends=len(ended), received_usage_records=len(usage),
            ADK_received={k:sum_known(usage,k) for k in ('prompt_token_count','candidates_token_count','total_token_count')},
            limitation='Role-tagged ADK usage only; may omit compaction and cancelled calls. Do not equate with total HTTP billing.')
    delegates = [r for r in tool_rows if r['actor']=='main_coding_agent' and r['tool']=='egv_verifier']
    incomplete_delegates = [dict(start_line=i,call_id=r['call_id'],start_seconds=seconds(r))
                           for i,r in starts.values() if r.get('tool')=='egv_verifier']
    edits = [r for r in tool_rows if r['production_candidate_changes']]
    if not folder.exists():
        status = 'not_run'
    elif audit.get('infrastructure_passed') and type(official.get('resolved')) is bool:
        status = 'resolved' if official['resolved'] else 'failed'
    else:
        status = 'unknown'
    result = dict(**row, normalized_status=status,
        native={k:official.get(k) for k in ('resolved','status','test_exit_code','duration_seconds','tool_calls','total_llm_calls','total_tokens','error_message')},
        infrastructure_passed=audit.get('infrastructure_passed'), infrastructure_reasons=audit.get('reasons'),
        Agent_elapsed_seconds=read(folder/'progress.json',{}).get('agent_elapsed_seconds'),
        first_production_candidate_edit_seconds=edits[0]['end_seconds'] if edits else None,
        first_production_candidate_edit_files=edits[0]['production_candidate_changes'] if edits else [],
        completed_delegations=len(delegates), incomplete_delegations=incomplete_delegates,
        delegation_events=[{k:d[k] for k in ('start_seconds','end_seconds','start_line','end_line','arguments','result')} for d in delegates],
        submit_tool_events=[{k:e[k] for k in ('start_seconds','end_seconds','start_line','end_line','result')} for e in tool_rows if e['tool']=='submit_patch'],
        model_usage_by_role=role_usage, actual_tool_start_events=sum(e['kind']=='tool_start' for e in nested),
        HTTP_terminal_counts=dict(Counter(r.get('status',r.get('terminal_status')) for r in terminal)),
        HTTP_received_only_usage={k:sum_known(received,k) for k in ('prompt_tokens','completion_tokens','total_tokens')},
        HTTP_usage_records=len(received), HTTP_terminal_records=len(terminal),
        usage_complete=bool(terminal) and len(received)==len(terminal) and all(not r.get('partial_usage') for r in terminal),
        closed_loop=None, valid_counterevidence=None, correctness_of_first_edit=None,
        interpretation='Descriptive extraction only. Manual issue/contract/tool/provenance/retest/native-result review required for algorithm and mechanism judgments.')
    emit(output / 'descriptive.json', result)
    return result


if __name__ == '__main__':
    candidates = [p for p in (HERE / 'download').rglob('*.zip') if p.stem[0:8].isdigit()]
    assert len(candidates) == 1, [str(p) for p in candidates]
    raw = candidates[0].read_bytes()
    proof = verify_zip(raw)
    target = HERE / 'results/gpu01'
    target.mkdir(parents=True, exist_ok=False)
    with (target / 'raw.zip').open('xb') as handle:
        handle.write(raw)
    with zipfile.ZipFile(candidates[0]) as z:
        for name in z.namelist():
            if name.endswith('/') or name.startswith('source/'):
                continue
            destination = target / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open('xb') as handle:
                handle.write(z.read(name))
    emit(HERE / 'RAW_COLLECTION.json', dict(source_archive=str(candidates[0].relative_to(HERE)), **proof))
    plan = read(HERE / 'AUTHORIZED_PROTOCOL.json')
    records = []
    for row in plan['runs']:
        folder = target / 'runs' / f"{row['index']:02d}-{row['instance_id']}-{row['arm']}"
        if folder.exists():
            records.append(inspect_run(folder, row))
        else:
            records.append(dict(**row,normalized_status='not_run',native=None,reason='No run directory; consult batch/session/setup exception.'))
    emit(HERE / 'GPU_RUN_LEDGER.json', dict(records=records, raw_archive_sha256=proof['sha256'],
        interpreted_by='Descriptive posthoc extraction; manual mechanism audit still required.'))
    emit(HERE / 'PAIR_COMPARISON.json', summarize(plan, target))
    print(json.dumps(dict(raw_sha256=proof['sha256'],runs=[{k:r.get(k) for k in ('instance_id','arm','normalized_status','first_production_candidate_edit_seconds','completed_delegations')} for r in records]),indent=2))
