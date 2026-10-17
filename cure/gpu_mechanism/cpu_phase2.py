"""CPU-only scripted Phase1 followed by real Phase2, in a fresh worker process."""
import asyncio
import json
from pathlib import Path
import sys
from unittest.mock import patch

if __name__=='__main__':
    from cure.worker import evaluate
    from harness_v2.official import DurableEvaluator
    spec=json.loads(Path(sys.argv[1]).read_text())
    reference=spec.pop('_cpu_reference_patch')
    async def scripted(evaluator,*args,**kwargs):
        # Preserve manager Agent/Verifier identity without running any LLM.
        sid=evaluator.docker.start()
        evaluator.docker.stop(sid)
        return reference,None,None
    out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=False)
    with patch.object(DurableEvaluator,'_run_agent_sandbox',scripted):
        asyncio.run(evaluate(spec,out))
