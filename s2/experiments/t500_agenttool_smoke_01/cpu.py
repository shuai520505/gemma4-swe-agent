"""Fresh official Linux native closed-loop and clean-task gate, no GPU."""
import asyncio
import json
from pathlib import Path
import sys
from harness_v2.evidence import atomic_json
from s2.egv_agenttool_t500_v01.session import require_cpu
from s2.egv_agenttool_t500_v01.environments import check
from s2.egv_agenttool_t500_v01.tests.runner_cases import exercise
from s2.egv_agenttool_t500_v01.nested_metrics import inspect_nested
from . import EXPERIMENT_ID


async def run(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    require_cpu(Path.cwd())
    protocol = json.loads(Path('s2/smoke_protocol.json').read_text())
    assert protocol['experiment_id'] == EXPERIMENT_ID
    actual = await exercise('closed_loop', output/'closed_loop', native=True, research_observer=True)
    nested = inspect_nested(output/'closed_loop')
    atomic_json(output/'closed_loop/nested_metrics.json', nested)
    assert actual['closed_loop'] and actual['explicit_submit'] and actual['HTTP']['passed']
    assert len(nested['delegations']) == 2 and not nested['child_workspace_side_effects']
    from s1.task_identity import identify, find_data
    assert identify(find_data(), protocol['task_inputs']) == protocol['task_inputs']
    baseline = await check(protocol['selected'][0], output/'baseline')
    assert baseline['eligible'] and baseline['cleanup_complete']
    atomic_json(output/'cpu_gate.json', dict(passed=True, experiment_id=EXPERIMENT_ID,
        closed_loop=True, explicit_submit=True, delegations=len(nested['delegations']),
        baseline_eligible=True, real_Gemma=False, GPU=False,
        candidate_zip_sha256=protocol['candidates']['B']['zip_sha256']))
    print('CPU_SMOKE_GATE_PASSED: real official tools; simulated HTTP, not Gemma', flush=True)


if __name__ == '__main__':
    asyncio.run(run(sys.argv[1]))
