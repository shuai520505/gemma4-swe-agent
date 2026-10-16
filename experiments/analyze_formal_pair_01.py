"""Audit both preregistered ZIPs and compute paired metrics without native edits."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from statistics import mean
import zipfile

from experiments.prepare import ROOT, write_new
from harness_v2.audit import audit


def token_fields(raw, events):
    # Pinned native TaskResult leaves total_tokens=0 despite nonzero ADK usage.
    # Keep the raw field; do not report that placeholder as measured zero cost.
    counts=[e['event']['usage_metadata']['total_token_count'] for e in events
            if (e.get('event',{}).get('usage_metadata') or {}).get('total_token_count') is not None]
    native=raw.get('total_tokens')
    return dict(native_total_tokens=native,total_tokens=native if native and native>0 else None,
        observed_native_usage_tokens=sum(counts) if counts else None,
        native_usage_responses=len(counts),token_accounting_scope='Observed ADK responses only; compaction usage may be absent')


def aggregate(rows):
    complete=len(rows)==8 and all(r['status'] in ('resolved','failed') and r.get('auditable') for r in rows)
    metrics={}
    for arm in ('v0','v1'):
        subset=[r for r in rows if r['arm']==arm]
        counts=Counter(r['status'] for r in subset)
        known=[r for r in subset if r['status'] in ('resolved','failed')]
        verified=[r for r in subset if r.get('phase2_execution')]
        m=dict(planned=4,status_counts=dict(counts),confirmed_verdicts=len(known),
            resolution_rate=counts['resolved']/4 if complete else None,
            patch_application_confirmed=sum(r.get('patch_application_confirmed') is True for r in subset),
            patch_application_rate=sum(r.get('patch_application_confirmed') is True for r in subset)/4 if complete else None,
            verifier_executions=len(verified),collection_failures=sum(r.get('failure_stage')=='test_collection' for r in verified),
            collection_failure_rate=sum(r.get('failure_stage')=='test_collection' for r in verified)/len(verified) if verified else None,
            agent_timeout_count=sum(r.get('agent_timeout',False) for r in subset),
            controller_errors=dict(Counter(r['controller_error'] for r in subset if r.get('controller_error'))))
        for field in ('llm_calls','tool_calls','duration_seconds','official_duration_seconds','total_tokens','observed_native_usage_tokens'):
            values=[r[field] for r in subset if isinstance(r.get(field),(int,float))]
            m[field]=dict(observed_n=len(values),mean=mean(values) if values else None,
                censored_n=sum((r.get('native_usage_responses',0)<r.get('context_admissions',0)) if field=='observed_native_usage_tokens' else r.get('counters_censored',False) if field in ('llm_calls','tool_calls','total_tokens') else r.get('controller_error') is not None for r in subset),
                missing_n=len(subset)-len(values))
        metrics[arm]=m
    pairs=[]
    for ident in sorted({r['instance_id'] for r in rows}):
        pair={r['arm']:r for r in rows if r['instance_id']==ident}
        known=set(pair)=={'v0','v1'} and all(r['status'] in ('resolved','failed') and r.get('auditable') for r in pair.values())
        winner=None
        if known:
            a,b=pair['v0']['status']=='resolved',pair['v1']['status']=='resolved'
            winner='tie' if a==b else ('v0' if a else 'v1')
        pairs.append(dict(instance_id=ident,complete=known,winner=winner))
    return dict(full_comparison_auditable=complete,arms=metrics,pairs=pairs,
        paired_wins=dict(Counter(p['winner'] for p in pairs)) if complete else None,
        interpretation='Exploratory four-task comparison only; no general superiority claim.' if complete else 'Incomplete experiment: no candidate superiority or full resolution rate is reported.')


def analyze(archives):
    protocol=json.loads((ROOT/'experiments/formal-paired-01/protocol.json').read_text())
    rows=[];archive_records=[]
    for letter,path in zip(('a','b'),archives):
        report_path=ROOT/f'harness_v2/results/paired01-{letter}-gpu-audit.json'
        report=json.loads(report_path.read_text()) if report_path.exists() else audit(path,'paired01-'+letter,'gpu')
        assert report['archive_sha256']==hashlib.sha256(path.read_bytes()).hexdigest()
        archive_records.append(dict(batch=letter,sha256=report['archive_sha256'],bytes=path.stat().st_size,path=str(path)))
        with zipfile.ZipFile(path) as z:
            if 'wheel_hashes.json' in z.namelist():assert json.loads(z.read('wheel_hashes.json'))==protocol['wheel_hashes']
            native_rows=json.loads(z.read('runs/audit_records.json')) if 'runs/audit_records.json' in z.namelist() else []
            for checked in report['runs']:
                row=dict(checked,batch=letter)
                native=next((r for r in native_rows if r['instance_id']==row['instance_id'] and r['arm']==row['arm']),{})
                row['patch_application_confirmed']=native.get('patch_application_confirmed')
                row['counters_censored']=native.get('counters_censored',True)
                row['total_tokens']=None;row['official_duration_seconds']=None
                prefix='runs/'+Path(native.get('run_directory','absent')).name+'/'
                if prefix+'official_result.json' in z.namelist():
                    raw=json.loads(z.read(prefix+'official_result.json'))
                    events=[json.loads(line) for line in z.read(prefix+'adk_events.jsonl').splitlines()] if prefix+'adk_events.jsonl' in z.namelist() else []
                    row.update(token_fields(raw,events))
                    row['official_duration_seconds']=raw.get('duration_seconds')
                    row['official_error']=raw.get('error_message')
                row['agent_timeout']='timeout' in str(row.get('official_error','')).lower() and 'session' in str(row.get('official_error','')).lower()
                row['auditable']=bool(row.get('official_result_present') and row.get('native_agent_trace') and row.get('frozen_prompt_matches') and row.get('required_model_only') and row.get('phase2_execution') and row.get('process_tree_stopped') and row.get('cleanup_complete'))
                rows.append(row)
    expected={(r['instance_id'],r['arm']) for r in protocol['schedule']}
    assert {(r['instance_id'],r['arm']) for r in rows}==expected and len(rows)==8
    result=dict(experiment_id=protocol['experiment_id'],protocol_sha256=hashlib.sha256((ROOT/'experiments/formal-paired-01/protocol.json').read_bytes()).hexdigest(),archives=archive_records,runs=rows,**aggregate(rows),official_competition_score=None)
    # Preserve the initial native-field audit. v2 corrects token interpretation.
    write_new(ROOT/'experiments/formal-paired-01/results-v2.json',(json.dumps(result,indent=2)+'\n').encode())
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('batch_a',type=Path);p.add_argument('batch_b',type=Path);a=p.parse_args()
    print(json.dumps(analyze([a.batch_a,a.batch_b]),indent=2))
