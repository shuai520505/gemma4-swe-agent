"""Task-paired native outcome statistics; missing data never become failures."""
import argparse
import json
import math
from pathlib import Path


def ratio(numerator, denominator):
    return numerator/denominator if denominator else None


def summarize(records, task_ids):
    def status(row):
        if row is None:return 'not_run'
        if not row.get('started',True):return 'not_run'
        if not row.get('infrastructure_passed'):return 'unknown'
        raw=row.get('official_result')
        if not raw or type(raw.get('resolved')) is not bool:return 'unknown'
        return 'resolved' if raw['resolved'] else 'failed'
    pairs=[]
    for task in task_ids:
        arms={arm:status(records.get((task,arm))) for arm in ('A','B')}
        pairs.append(dict(instance_id=task,**arms,auditable=all(v in ('resolved','failed') for v in arms.values())))
    valid=[p for p in pairs if p['auditable']]
    wins=sum(p['A']=='failed' and p['B']=='resolved' for p in valid)
    losses=sum(p['A']=='resolved' and p['B']=='failed' for p in valid)
    same_success=sum(p['A']==p['B']=='resolved' for p in valid)
    same_failure=sum(p['A']==p['B']=='failed' for p in valid)
    n=wins+losses
    complete=len(valid)==len(task_ids)==8
    return dict(task_pairs=pairs,auditable_pairs=len(valid),planned_pairs=len(task_ids),complete_eight_task_experiment=complete,
        B_only_resolved=wins,A_only_resolved=losses,both_resolved=same_success,both_failed=same_failure,
        paired_difference_on_observed_pairs=ratio(wins-losses,len(valid)),
        full_experiment_resolution_rates=dict(A=(same_success+losses)/8,B=(same_success+wins)/8) if complete else None,
        exact_discordant_sign_test_p=min(1.,2*sum(math.comb(n,k) for k in range(min(wins,losses)+1))/2**n) if n else None,
        interpretation='Eight selected tasks remain small, nonrandom population sample; tool calls are not independent task replicates. Incomplete pairs do not establish a full success rate.')


def mechanism(annotations):
    # Human tool-trajectory audit, not model report assertions. Each eligible
    # row must cite immutable native tool records, supplied by separate review.
    qualified=[r for r in annotations if r.get('actionable') and r.get('evidence_level') in (1,2) and r.get('discovery_tool_pointer')]
    delivered=[r for r in qualified if r.get('delivery_tool_pointer')]
    handled=[r for r in delivered if r.get('main_action_tool_pointer')]
    closed=[r for r in handled if r.get('main_action_kind')=='production_edit'
        and r.get('retest_tool_pointer') and r.get('counterevidence_eliminated') is True]
    return dict(actionable=len(qualified),delivered=len(delivered),handled=len(handled),closed=len(closed),
        delivery_rate=ratio(len(delivered),len(qualified)),handling_rate=ratio(len(handled),len(delivered)),
        closed_loop_rate=ratio(len(closed),len(delivered)),
        scope='Pointers require independent content/validity/provenance review; schema completeness alone does not certify a valid probe.')


def main(protocol, results, output):
    plan=json.loads(Path(protocol).read_text());rows={}
    for r in plan['runs']:
        directory=Path(results)/f"{r['index']:02d}-{r['instance_id']}-{r['arm']}"
        if not directory.exists():continue
        audit=directory/'research_audit.json';official=directory/'official_result.json'
        rows[(r['instance_id'],r['arm'])]=dict(started=True,
            infrastructure_passed=json.loads(audit.read_text()).get('infrastructure_passed',False) if audit.exists() else False,
            official_result=json.loads(official.read_text()) if official.exists() else None)
    result=summarize(rows,[r['instance_id'] for r in plan['selected']])
    Path(output).write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('protocol');p.add_argument('results');p.add_argument('output')
    a=p.parse_args();main(a.protocol,a.results,a.output)
