"""Reuse official worker and passive EGR observer; frozen PR26 result reader."""
import asyncio,inspect,json,sys,types
from pathlib import Path
from unittest.mock import patch

async def evaluate(spec,directory):
    from u_re.v04.experiments.evidence_guided_repair_01 import worker as accepted
    from u_re.v01.experiments.action_priority_01.real_gemma_abba03 import worker as transport
    from u_re.v01.experiments.action_priority_01.real_gemma_abba01 import worker as original
    code=inspect.getsource(original.evaluate)
    old='from s1.verifier_v3.audit import audit_verifier'
    assert code.count(old)==1
    code=code.replace(old,'from u_re.v02.experiments.env_recovery_admission_01.junit_audit import audit_verifier')
    namespace=dict(original.__dict__);exec(compile(code,'<Same-worker-frozen-PR26-research-reader>','exec'),namespace)
    # Only research result interpretation changes. Official verify_task, test
    # bytes, verdict, tools, patch and model interactions remain untouched.
    with patch.object(transport,'_evaluate',namespace['evaluate']):await accepted.evaluate(spec,directory)

if __name__=='__main__':
    directory=Path(sys.argv[2]);directory.mkdir(parents=True,exist_ok=True)
    try:asyncio.run(evaluate(json.loads(Path(sys.argv[1]).read_bytes()),directory))
    except BaseException as exc:
        import traceback
        from harness_v2.evidence import atomic_json
        atomic_json(directory/'worker_exception.json',dict(type=type(exc).__name__,error=str(exc),traceback=traceback.format_exc()));raise
