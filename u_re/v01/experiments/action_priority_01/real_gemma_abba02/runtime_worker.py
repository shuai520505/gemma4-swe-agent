"""Reuse production worker; keep passive HTTP logs outside Runner-owned creation."""
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch
from s1.infrastructure_recovery import wire
from ..real_gemma_abba01 import worker

_observe=wire.observe_http
_evaluate=worker.evaluate

@contextmanager
def observe_without_precreating_agent(directory):
    directory=Path(directory)
    transport=directory.parent/'model_transport'
    # The official Agent phase exclusively creates directory. No tool or Runner
    # semantic is changed. Only passive HTTP persistence uses a sibling folder.
    with _observe(transport):
        try:yield
        finally:
            for name in ('http_wire.jsonl','http_lifecycle.jsonl'):
                source=transport/name
                if source.exists():
                    assert directory.is_dir() and not (directory/name).exists()
                    source.replace(directory/name) # Preserve exact original event bytes.

async def evaluate(spec,directory):
    with patch.object(wire,'observe_http',observe_without_precreating_agent):
        return await _evaluate(spec,directory)

if __name__=='__main__':
    import asyncio,json,sys
    directory=Path(sys.argv[2]);directory.mkdir(parents=True,exist_ok=True)
    asyncio.run(evaluate(json.loads(Path(sys.argv[1]).read_bytes()),directory))
