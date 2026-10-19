"""Assumption-labelled12h scheduling scenarios; never Gemma observations."""
import csv
import json
import math
from pathlib import Path
import random

HERE=Path(__file__).resolve().parent


def scenario(n,setup,cap_fraction,early_seconds,*,seed=17,repeats=1000):
    rng=random.Random(seed);missed=[];durations=[];timely=[]
    for _ in range(repeats):
        # Random order is a sensitivity assumption; actual scoring order and
        # scheduling concurrency are not exposed by the public API.
        times=[500 if rng.random()<cap_fraction else early_seconds for _ in range(n)]
        rng.shuffle(times);spent=600;completed=0;submitted=0
        for duration in times:
            if spent+setup+duration>43200:break
            spent+=setup+duration;completed+=1
            # Hypothesis only: all early finishes explicitly submit, cap cases
            # do not. This is not an empirical submission probability.
            submitted+=duration<500
        missed.append(n-completed);timely.append(submitted/n);durations.extend(times)
    durations.sort()
    q=lambda p:durations[min(len(durations)-1,math.ceil(p*len(durations))-1)]
    return dict(tasks=n,setup_seconds=setup,cap_fraction_assumed=cap_fraction,
        early_seconds_assumed=early_seconds,P50_assumed=q(.5),P90_assumed=q(.9),P95_assumed=q(.95),
        average_agent_seconds_assumed=(1-cap_fraction)*early_seconds+cap_fraction*500,
        mean_not_run=sum(missed)/repeats,max_not_run=max(missed),
        probability_any_not_run_conditional=sum(x>0 for x in missed)/repeats,
        probability_at_least20percent_not_run_conditional=sum(x>=math.ceil(.2*n) for x in missed)/repeats,
        timely_submit_fraction_assumed=sum(timely)/repeats,concurrency_assumed=1,repeats=repeats,
        global_reserve_seconds_assumed=600,cap_patch_missing_probability_assumed=.5,
        early_patch_missing_probability_assumed=.05,
        expected_patch_missing_among_started_assumed=(1-cap_fraction)*.05+cap_fraction*.5,
        scope='Conditional Monte Carlo under unvalidated workload assumptions, not actual risk probability or GPU measurement.')


def main():
    rows=[scenario(n,setup,p,early) for n in (60,80,100,120,140,160)
          for setup in (5,20,60) for p in (.25,.5,.75,1.) for early in (120,240)]
    with (HERE/'GLOBAL_BUDGET_SCENARIOS.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator="\n");w.writeheader();w.writerows(rows)
    evidence=dict(total_seconds=43200,official_test_count='About120 total, evenly public/private; not exactly129 or a confirmed per-rerun count.',
        hidden_scheduler_concurrency='NOT_EXPOSED; serial is conservative sensitivity, not a verified scoring topology.',
        actual_T500_GPU_observations=0,empirical_P50=None,empirical_P90=None,empirical_P95=None,
        empirical_cap_fraction=None,empirical_explicit_submit_fraction=None,empirical_delegation_cost=None,
        empirical_main_retest_reserve=None,probability_of_actual_budget_exhaustion=None,
        scenarios=len(rows),large_loss_definition='At least20% tasks unrun in a conditional scenario.',
        release_rule='NoGo if verified task scheduling and representative matched T500 timing support >=90% probability of >=20% unrun tasks. Do not treat assumed Monte Carlo frequencies as empirical probability. Report worst-case envelope and unresolved risk before any single exploratory official submission.',
        full_cap_serial_capacity={str(s):43200//(500+s) for s in (5,20,60)},
        full_cap_serial_capacity_with600second_reserve={str(s):42600//(500+s) for s in (5,20,60)},
        expected_mean_agent_requirement_for120={str(s):43200/120-s for s in (5,20,60)},
        score_causality='S0 vs T500 changes architecture/prompts/time. A single score cannot identify time or AgentTool causal benefit.')
    (HERE/'GLOBAL_BUDGET_MODEL.json').write_bytes((json.dumps(evidence,indent=2)+'\n').encode())
    print('Wrote',len(rows),'assumption-labelled scenarios; no empirical GPU percentile/risk invented.')


if __name__=='__main__':main()
