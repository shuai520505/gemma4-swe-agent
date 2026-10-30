import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HERE=Path(__file__).resolve().parent
ORDER=[('django__django-16333','S0'),('django__django-16333','SUPERAGENT'),
       ('pydata__xarray-3095','SUPERAGENT'),('pydata__xarray-3095','S0'),
       ('fastapi_14297','S0'),('fastapi_14297','SUPERAGENT')]
HASHES={'S0':'3303d6e1dd246d3861910701beb580c8d9a165ea1eb1c1a13d8c8ba9d6efd4f9',
        'SUPERAGENT':'944e1d23ce5e93a77af3e993834487e829487aff0a92ec7fe3e115590bfaf9f1'}

def sha(body):return hashlib.sha256(body).hexdigest()

def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n',encoding='utf8')

def package(name,destination,model_path):
    import zipfile
    import yaml
    from adk_submission import ModelRegistry,compile_submission,validate_directory
    from google.adk.models.lite_llm import LiteLlm
    from swegemma.config import build_submission_limits
    from swegemma.context import SwegemmaContext
    raw=(ROOT/'paired_candidates'/(name+'.zip')).read_bytes();assert sha(raw)==HASHES[name]
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=False)
    with zipfile.ZipFile(__import__('io').BytesIO(raw)) as z:
        assert z.testzip() is None
        assert all(not n.startswith('/') and '..' not in Path(n).parts for n in z.namelist())
        z.extractall(destination)
    budget=yaml.safe_load((destination/'eval_config.yaml').read_text())['evaluation']
    registry=ModelRegistry();label='gemma-4-31b-it-qat-w4a16-ct'
    registry.register(label,LiteLlm(model='openai/'+model_path,api_base='http://127.0.0.1:8000/v1',api_key='EMPTY'))
    limits,constraints=build_submission_limits();validate_directory(destination,limits=limits)
    compiled=compile_submission(destination,SwegemmaContext().create_tools(),registry,limits=limits,generation_constraints=constraints)
    assert not compiled.sub_agents
    assert budget['max_time_minutes']==(5 if name=='S0' else 8)
    assert budget['max_tool_calls']==(60 if name=='S0' else 28)
    assert budget['timeout_seconds']==(120 if name=='S0' else 240)
    return registry,limits,constraints,compiled,budget

def config(candidate,registry,limits,constraints,budget,taskfile,snapshot,wheels,out):
    from swegemma.config import EvalConfig
    from google.adk.agents.context_cache_config import ContextCacheConfig
    from google.adk.apps._configs import EventsCompactionConfig
    cfg=EvalConfig(tasks_path=Path(taskfile),snapshots_dir=Path(snapshot).parent,results_dir=Path(out)/'harness',
        submission_dir=Path(candidate),models=registry,sandbox='subprocess',wheels_dir=Path(wheels),
        max_time_minutes=budget['max_time_minutes'],max_tool_calls=budget['max_tool_calls'],max_turns=budget.get('max_turns'),
        timeout_seconds=budget['timeout_seconds'],verification_timeout_seconds=300,
        limits=limits,generation_constraints=constraints,enable_sandbox_testing=True,display_mode='quiet',
        events_compaction_config=EventsCompactionConfig(compaction_interval=15,overlap_size=2,
            token_threshold=14336,event_retention_size=5),
        context_cache_config=ContextCacheConfig(min_tokens=2048,ttl_seconds=1800,cache_intervals=10))
    if 'max_turns' in budget:
        assert cfg.budget.turns==budget['max_turns']
    assert cfg.budget.time_minutes==budget['max_time_minutes']
    assert cfg.budget.tool_calls==budget['max_tool_calls']
    assert cfg.harness.command_timeout_seconds==budget['timeout_seconds']
    return cfg
