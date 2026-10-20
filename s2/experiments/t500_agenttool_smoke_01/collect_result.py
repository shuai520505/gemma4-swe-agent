"""Offline immutable collection and tool ledger; no model-prose success inference."""
import csv
import io
import json
from pathlib import Path
import sys
import zipfile
from experiments.prepare import write_new
from s1.collect import verify_zip
from harness_v2.evidence import read_events

HERE=Path(__file__).resolve().parent


def dump(path,value):
    write_new(path,(json.dumps(value,indent=2)+'\n').encode())


def collect(path):
    raw=Path(path).read_bytes();proof=verify_zip(raw)
    target=HERE/'results/gpu01'
    write_new(target/'raw.zip',raw)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        for n in z.namelist():
            if n.endswith('/') or n.startswith('source/') or 'snapshot_source' in Path(n).parts or '.git' in Path(n).parts:continue
            write_new(target/n,z.read(n))
    dump(target/'collection.json',proof)
    runs=list((target/'runs').glob('*-rich_3471-B'))
    if not runs:
        dump(target/'OFFLINE_SUMMARY.json',dict(task_status='not_run',
            reason='No task worker directory; inspect startup/environment failure evidence',
            Gemma_task_reasoning_verified=False,paired_experiment=False))
        return
    assert len(runs)==1
    run=runs[0]
    def load(name):
        p=run/name
        return json.loads(p.read_text()) if p.exists() else None
    raw_result=load('official_result.json');audit=load('research_audit.json')
    events=read_events(run/'nested_audit.jsonl');stage=read_events(run/'events.jsonl')
    origins=[r['recorded_monotonic'] for r in stage if r.get('kind')=='stage' and r.get('stage')=='agent']
    origin=min(origins) if origins else min((r['monotonic'] for r in events),default=0)
    starts={};ledger=[]
    for line,r in enumerate(events,1):
        if r['kind']=='tool_start':starts[(r['actor'],r['call_id'])]=(line,r)
        if r['kind'] not in ('tool_end','tool_error'):continue
        matched=starts.pop((r['actor'],r.get('call_id')),None)
        if not matched:continue
        start_line,s=matched
        files_before=s.get('files',{});files_after=r.get('files',{})
        changes=sorted(n for n in set(files_before)|set(files_after) if files_before.get(n)!=files_after.get(n)) if r['kind']=='tool_end' else None
        ledger.append(dict(actor=r['actor'],tool=r['tool'],call_id=r.get('call_id'),
            started_seconds=s['monotonic']-origin,ended_seconds=r['monotonic']-origin,
            seconds=r['monotonic']-s['monotonic'],args=s.get('args'),result=r.get('result'),error=r.get('error'),
            changed_files=changes,counted_delta=r['counted_tools']-s['counted_tools'],
            start_pointer=f'nested_audit.jsonl:{start_line}',end_pointer=f'nested_audit.jsonl:{line}',
            behavioral_validity='requires independent tool-content review'))
    dump(target/'TOOL_LEDGER.json',ledger)
    status=(audit or {}).get('outcome',{}).get('status','unknown')
    if status not in ('resolved','failed','unknown','not_run'):status='unknown'
    dump(target/'OFFLINE_SUMMARY.json',dict(task_status=status,
        infrastructure_passed=(audit or {}).get('infrastructure_passed'),
        official_result={k:raw_result.get(k) for k in ('resolved','status','test_exit_code','duration_seconds','total_llm_calls','total_tokens','tool_calls')} if raw_result else None,
        observed_usage=(audit or {}).get('usage'),usage_complete=(audit or {}).get('usage_complete'),
        partial_token_usage=(audit or {}).get('partial_token_usage'),
        nested=load('nested_metrics.json'),worker_cleanup=load('worker_done.json'),
        explicit_submit_observed=any(r['actor']=='main_coding_agent' and r['tool']=='submit_patch' for r in ledger),
        first_main_workspace_mutation_seconds=next((r['ended_seconds'] for r in ledger if r['actor']=='main_coding_agent' and r['tool'] in ('edit_file','write_file','run_command') and r['changed_files']),None),
        mechanism_success='NOT_AUTOMATICALLY_INFERRED: inspect code diff, child execution, Main edits and real retest',
        paired_experiment=False,population_resolution_rate=None))
    print(json.dumps(dict(proof=proof,run=str(run),status=status),indent=2))


if __name__=='__main__':collect(sys.argv[1])
