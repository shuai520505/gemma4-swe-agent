"""Two metadata-selected clean native baselines, no Agent/model/GPU."""
import asyncio
import json
from pathlib import Path
import sys
from harness_v2.evidence import atomic_json
from s1.task_identity import find_data,identify
from s2.egv_agenttool_t500_v01.environments import check


async def run(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    pool=json.loads(Path('s2/early_task_pool.json').read_text())
    assert not pool['GPU_authorized'] and not pool['reference_repair_read']
    assert identify(find_data(),pool['task_inputs'])==pool['task_inputs']
    records=[]
    for row in pool['selected']:
        r=await check(row,output/row['instance_id']);records.append(r)
        atomic_json(output/'progress.json',records)
        if not r['eligible'] or not r['cleanup_complete']:break
    gate=dict(passed=len(records)==2 and all(r['eligible'] and r['cleanup_complete'] for r in records),
        records=records,Agent_runs=0,GPU=False,reference_repair_read=False,
        interpretation='Native clean-baseline eligibility only; not repair successes. No task substitution after this selection.')
    atomic_json(output/'environment_gate.json',gate)
    assert gate['passed'],'Selected task ineligible; stop rather than substitute'
    print('EARLY_TWO_TASK_ENVIRONMENT_GATE_PASSED',flush=True)


if __name__=='__main__':asyncio.run(run(sys.argv[1]))
