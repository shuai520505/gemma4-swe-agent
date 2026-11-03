"""Actual SDK budget/status API check; no Runner, sandbox, model or GPU."""
import json,time
from pathlib import Path
from types import SimpleNamespace
from swegemma.context import SwegemmaContext
from swegemma.tools.execution import get_status
from timing import align_context
D=Path(__file__).resolve().parent
ctx=SwegemmaContext(max_time_minutes=5,max_tool_calls=60,max_exec_seconds=120)
ctx.start_agent_session();raw=ctx.agent_start_time
now=time.monotonic();receipt=dict(captured=True,deadline_origin_monotonic=now-4.7,deadline_monotonic=now+295.3)
align_context(ctx,SimpleNamespace(receipt=receipt));status=json.loads(get_status(ctx))
assert ctx.raw_sdk_agent_start_time==raw and ctx.budget.time_minutes==5
assert 294<status['time_seconds_remaining']<296 and status['max_time_minutes']==5
assert status['agent_elapsed_seconds']>=4.7 and status['command_timeout_seconds']==120
out=dict(status='PASS',scope='Actual SwegemmaContext/get_status API with a4.7s timing fixture; full nonroot SDK Runner remains NOT_RUN',official_status=status,original_context_start=raw,aligned_context_start=ctx.agent_start_time,SDK_budget_seconds=300,real_model_requests=0,GPU=0)
(D/'evidence/SDK_CONTEXT_CLOCK_CHECK.json').write_text(json.dumps(out,indent=2));print('SDK_CONTEXT_CLOCK_CHECK_PASS')
