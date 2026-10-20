"""Prospective two-pair accounting; missing data never becomes a failed repair."""
import json
from pathlib import Path
import sys
from s2.egv_agenttool_t500_v01.analyze import mechanism


def summarize(plan,root):
    root=Path(root);pairs=[]
    for task in (r['instance_id'] for r in plan['selected']):
        statuses={}
        for arm in ('A','B'):
            row=next(r for r in plan['runs'] if r['instance_id']==task and r['arm']==arm)
            p=root/'runs'/f"{row['index']:02d}-{task}-{arm}"
            if not p.exists():statuses[arm]='not_run';continue
            raw=p/'official_result.json';audit=p/'research_audit.json'
            if not raw.exists() or not audit.exists() or not json.loads(audit.read_text()).get('infrastructure_passed'):
                statuses[arm]='unknown';continue
            resolved=json.loads(raw.read_text()).get('resolved')
            statuses[arm]=('resolved' if resolved else 'failed') if type(resolved) is bool else 'unknown'
        pairs.append(dict(instance_id=task,**statuses,
            auditable=all(s in ('resolved','failed') for s in statuses.values())))
    complete=bool(pairs) and all(p['auditable'] for p in pairs)
    wins=sum(p['A']=='failed' and p['B']=='resolved' for p in pairs)
    losses=sum(p['A']=='resolved' and p['B']=='failed' for p in pairs)
    return dict(task_pairs=pairs,complete_prespecified_pairs=complete,
        B_only_resolved=wins,A_only_resolved=losses,
        observed_paired_difference=(wins-losses)/len(pairs) if complete else None,
        population_resolution_rate=None,
        interpretation='Two selected tasks are exploratory; native results are primary. No incomplete-pair success rate or population-superiority claim.')


if __name__=='__main__':
    plan=json.loads(Path(sys.argv[1]).read_text())
    print(json.dumps(summarize(plan,sys.argv[2]),indent=2))
