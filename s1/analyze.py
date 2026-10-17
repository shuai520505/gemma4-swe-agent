"""Offline, missingness-aware paired analysis. Never selects/restarts task runs."""
import argparse
from collections import Counter
import json
from pathlib import Path
from .util import save


def summarize(plan,records):
    by_index={r['index']:r for r in records}
    if len(by_index)!=len(records):raise ValueError('Duplicate run index; retries must not be spliced')
    rows=[]
    for batch,schedule in plan['batches'].items():
        for r in schedule:
            actual=by_index.get(r['index'])
            if actual:
                if any(actual[k]!=r[k] for k in ('arm','instance_id')):
                    raise ValueError('Run identity drift')
                audit=actual['audit']
                rows.append(dict(**r,batch=batch,status=audit['outcome']['status'],audit=audit))
            else:rows.append(dict(**r,batch=batch,status='not_run',audit=None))
    screened=[r for r in rows if r['batch']!='smoke']
    task_ids=list(dict.fromkeys(r['instance_id'] for r in screened))
    pairs=[]
    for task in task_ids:
        selected={r['arm']:r for r in screened if r['instance_id']==task}
        complete=len(selected)==2 and all(r['status'] in ('resolved','failed') and
            r['audit']['infrastructure_passed'] for r in selected.values())
        pairs.append(dict(instance_id=task,complete=complete,
            control=selected['control']['status'],e1=selected['e1_output8192']['status']))
    all_complete=bool(pairs) and all(p['complete'] for p in pairs)
    a_only=sum(p['control']=='resolved' and p['e1']=='failed' for p in pairs if p['complete'])
    b_only=sum(p['e1']=='resolved' and p['control']=='failed' for p in pairs if p['complete'])
    both=sum(p['control']==p['e1']=='resolved' for p in pairs if p['complete'])
    counts={arm:{s:sum(r['arm']==arm and r['status']==s for r in screened)
            for s in ('resolved','failed','unknown','not_run')}
            for arm in ('control','e1_output8192')}
    return dict(experiment_id=plan['experiment_id'],scope='public development screening; smoke excluded from primary',
        planned_screen_pairs=len(pairs),complete_screen_pairs=sum(p['complete'] for p in pairs),
        all_pairs_complete=all_complete,counts=counts,pairs=pairs,all_slots=rows,
        primary_resolved_difference=(b_only-a_only)/len(pairs) if all_complete else None,
        full_resolution_rates={a:counts[a]['resolved']/len(pairs) if all_complete else None for a in counts},
        discordant=dict(control_only=a_only,e1_only=b_only,both_resolved=both,
            scope='Observed complete pairs only; not a replacement for the planned denominator'),
        sufficient_for_S1_freeze=False,
        warning='Four selected development pairs cannot by themselves establish robust improvement or hidden leaderboard gain')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('protocol');p.add_argument('output');p.add_argument('records',nargs='*')
    a=p.parse_args();records=[]
    for f in a.records:records+=json.loads(Path(f).read_text())
    summary=summarize(json.loads(Path(a.protocol).read_text()),records)
    save(Path(a.output),summary)
    print(json.dumps({k:v for k,v in summary.items() if k not in ('all_slots',)},indent=2))
