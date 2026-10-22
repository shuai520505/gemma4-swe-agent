"""Revised real official CPU acceptance plus independent kernel-isolation test."""
import asyncio
import json
from pathlib import Path
import sys
import traceback

async def run(output):
    from harness_v2.evidence import atomic_json
    from ..cpu_interfaces import run as corrected_acceptance
    from .cpu_isolation import run as isolation_test
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    records=[]
    for name,fn in (('official_acceptance',corrected_acceptance),('kernel_isolation',isolation_test)):
        try:
            await fn(output/name);records.append(dict(stage=name,passed=True))
        except BaseException as exc:
            atomic_json(output/(name+'_error.json'),dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc()))
            records.append(dict(stage=name,passed=False,error_class=type(exc).__name__))
    result=dict(passed=all(r['passed'] for r in records),stages=records,
        GPU=False,Gemma_inference=False,competition_task_executed=False,
        old_CPU01_status='ERROR_UNCHANGED',algorithm_validated=False)
    atomic_json(output/'RECOVERY_GATE.json',result)
    print(json.dumps(result),flush=True)
    if not result['passed']:raise RuntimeError('CPU recovery gate failed; preserve results, no automatic resave')

if __name__=='__main__':asyncio.run(run(sys.argv[1]))
