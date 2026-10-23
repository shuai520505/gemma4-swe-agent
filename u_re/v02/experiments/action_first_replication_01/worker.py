"""Use byte-identical GPU03 evaluation logic and passive HTTP persistence."""
from u_re.v01.experiments.action_priority_01.real_gemma_abba03.worker import evaluate

if __name__=='__main__':
    import asyncio,json,sys,traceback
    from pathlib import Path
    from harness_v2.evidence import atomic_json
    directory=Path(sys.argv[2]);directory.mkdir(parents=True,exist_ok=True)
    try:asyncio.run(evaluate(json.loads(Path(sys.argv[1]).read_bytes()),directory))
    except BaseException as exc:
        atomic_json(directory/'worker_exception.json',dict(type=type(exc).__name__,error=str(exc),traceback=traceback.format_exc()));raise
