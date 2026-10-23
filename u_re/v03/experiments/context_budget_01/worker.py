"""Minimal research configuration adapter around unchanged official execution."""
import inspect,json,sys,asyncio
from pathlib import Path
from .policy import budget,research_candidate
from u_re.v01.experiments.action_priority_01.real_gemma_abba01 import worker as legacy
from u_re.v01.experiments.action_priority_01.real_gemma_abba03.worker import observe_without_precreating_agent
from s1.infrastructure_recovery import wire
from harness_v2.evidence import atomic_json
from unittest.mock import patch

async def evaluate(spec,directory):
    directory=Path(directory)
    spec=dict(spec)
    original=Path(spec['agent_dir'])
    spec['agent_dir']=str(research_candidate(original,directory/'research_candidate',spec['arm']))
    code=inspect.getsource(legacy.evaluate)
    old='budget=Config();data='
    assert code.count(old)==1
    code=code.replace(old,"budget=policy_budget(spec['arm']);data=")
    namespace=dict(legacy.__dict__,policy_budget=budget)
    exec(compile(code,'<V03-single-output-cap-research-config>','exec'),namespace)
    with patch.object(wire,'observe_http',observe_without_precreating_agent):
        await namespace['evaluate'](spec,directory)
    path=directory/'runtime_config.json';cfg=json.loads(path.read_bytes())
    cfg.update(real_model=spec['model_transport']=='REAL_GEMMA',model_transport=spec['model_transport'],context_policy=spec['arm'],original_candidate_sha256=spec['candidate_sha256'])
    assert cfg['budget']['output_tokens']==cfg['generation']['max_output_tokens']==budget(spec['arm']).output_tokens
    atomic_json(path,cfg)

if __name__=='__main__':
    directory=Path(sys.argv[2]);directory.mkdir(parents=True,exist_ok=True)
    try:asyncio.run(evaluate(json.loads(Path(sys.argv[1]).read_bytes()),directory))
    except BaseException as exc:
        import traceback
        atomic_json(directory/'worker_exception.json',dict(type=type(exc).__name__,error=str(exc),traceback=traceback.format_exc()));raise
