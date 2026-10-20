"""Deterministic assumptions, not empirical probabilities or scored outcomes."""
import csv
import io
import json
from pathlib import Path
from .build import HERE,write


def scenario(n,short,tail,setup,teardown,startup,verify):
    mean=(1-tail)*short+tail*300
    patch=n*(mean+setup)+600
    # Final diff/tests/submission are already inside Agent time. Teardown here
    # means post-Agent sandbox/persistence, not double-counted Agent Closure.
    platform_without_verification=startup+n*(mean+setup+teardown)+900
    return dict(tasks=n,short_agent_seconds=short,full_cap_fraction=tail,
        assumed_mean_agent_seconds=mean,setup_seconds_per_task=setup,
        post_agent_lifecycle_seconds_per_task=teardown,bootstrap_seconds=startup,
        native_verifier_seconds_per_task=verify,patch_reserve_seconds=600,
        patch_budget_total_seconds=patch,patch_fits_12h=patch<=43200,
        platform_seconds_if_verification_outside_window=platform_without_verification,
        platform_seconds_if_serial_verification_inside_window=platform_without_verification+n*verify,
        platform_window_seconds=None,platform_fits='UNKNOWN_WINDOW_AND_SCHEDULING',
        status='ASSUMPTION_SENSITIVITY_NOT_EMPIRICAL_PROBABILITY')


def build():
    rows=[scenario(n,short,tail,setup,10,1200,verify)
          for n in (60,80,100,120,140) for short in (90,180)
          for tail in (.25,.5,.75,1.) for setup in (5,20,60) for verify in (30,120,300)]
    out=io.StringIO(newline='');writer=csv.DictWriter(out,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    write(HERE/'GLOBAL_BUDGET_SCENARIOS.csv',out.getvalue().encode())
    summary=dict(scope='No U-RE Gemma durations yet. Two selected S2 tasks do not calibrate these assumptions.',
        GPU_status='GPU_NOT_TESTED',scenarios=len(rows),mean_envelopes=[dict(tasks=n,
            patch_mean_agent_plus_setup_max_without_reserve=43200/n,
            patch_mean_agent_plus_setup_max_with_600s_reserve=42600/n,
            agent_mean_max_if_setup20s=42600/n-20,
            all300s_plus20s_setup_with_reserve=n*320+600,
            all300s_plus20s_setup_fits=n*320+600<=43200) for n in (60,80,100,120,140)],
        empirical_quantiles=dict(P50=None,P90=None,P95=None,cap_fraction=None,successful_submit_fraction=None),
        formal_submission='NO_GO_UNTIL_TOTAL_WINDOW_AND_REPRESENTATIVE_THROUGHPUT_VERIFIED',
        verifier_window='Official patch budget excludes verification according to carried-forward competition rule; private scoring process and platform runtime/scheduling remain independently unverified.')
    write(HERE/'GLOBAL_BUDGET_MODEL.json',(json.dumps(summary,indent=2)+'\n').encode())


if __name__=='__main__':
    build()
