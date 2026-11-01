"""Opt-in host composition; never edits frozen worker/SDK or submission ZIP."""
import asyncio,json,sys
from pathlib import Path
from unittest.mock import patch
import r2a_worker as frozen
import r2a_runtime
from hardened_runtime import SubprocessManager,DurableContext
async def run(spec,out):
    with patch.object(frozen,'SubprocessManager',SubprocessManager),patch.object(frozen,'DurableContext',DurableContext),patch.object(r2a_runtime,'SubprocessManager',SubprocessManager):
        try:await frozen.run(spec,out)
        finally:
            p=Path(out)/'SESSION_RESULT.json';receipt=Path(out)/'INFRASTRUCTURE_STOP.json'
            if p.exists():
                row=json.loads(p.read_bytes());row['infrastructure_stop']=json.loads(receipt.read_bytes()) if receipt.exists() else None
                r2a_runtime.write(p,row)
if __name__=='__main__':asyncio.run(run(json.loads(Path(sys.argv[1]).read_bytes()),sys.argv[2]))
