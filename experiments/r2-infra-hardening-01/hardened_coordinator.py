"""Prospective opt-in coordinator, not a Notebook dispatcher or new experiment."""
import asyncio,sys
from unittest.mock import patch
import r2a_coordinator as frozen
import gemma_pair.coordinator as prior
from stop_policy import admission
async def run(out,started):
    legacy=frozen.admission;run_prior=prior.run
    async def composed(out,started,plan):
        plan=dict(plan,worker_module='hardened_worker');return await run_prior(out,started,plan)
    with patch.object(frozen,'admission',lambda row,outcome:admission(row,outcome,legacy)),patch.object(prior,'run',composed):
        await frozen.run(out,started)
if __name__=='__main__':asyncio.run(run(sys.argv[1],float(sys.argv[2])))
