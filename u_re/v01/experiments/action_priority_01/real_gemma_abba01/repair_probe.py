"""CPU-only targeted package/import/compiler/boundary probe;zero Agent/model/task runs."""
import hashlib
import importlib
import inspect
import json
from pathlib import Path
import shlex
import sys

from harness_v2.evidence import Journal,atomic_json

def run(output):
    import torch
    assert torch.cuda.device_count()==0,'CPU repair refuses GPU'
    from adk_submission import ModelRegistry,compile_submission
    from google.adk.models.lite_llm import LiteLlm
    from swegemma.context import SwegemmaContext
    from swegemma.config import build_submission_limits
    from s1.config import Config,validate_compiled
    from s1.task_identity import find_data
    from .GPU_NOTEBOOK import ROOT,PRIOR
    from .worker import SubprocessManager
    from .ISOLATION_CANARY import CANARY
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    lock=json.loads((PRIOR/'ABBA_EXPERIMENT_LOCK.json').read_bytes())
    for n,h in lock['source_pins'].items():assert hashlib.sha256((PRIOR/n).read_bytes()).hexdigest()==h,n
    for n,h in lock['native_verifier_source_sha256'].items():assert hashlib.sha256(Path(inspect.getfile(importlib.import_module(n))).read_bytes()).hexdigest()==h
    limits,constraints=build_submission_limits();registry=ModelRegistry()
    registry.register('gemma-4-31b-it-qat-w4a16-ct',LiteLlm(model='openai/gemma-4-31b-it-qat-w4a16-ct',api_base='http://127.0.0.1:9/v1',api_key='EMPTY'))
    compiled=[]
    for directory in (ROOT/'u_re/v01/candidate_noegv',ROOT/'u_re/v01/experiments/action_priority_01/candidate_action_v01'):
        agent=compile_submission(directory,SwegemmaContext().create_tools(),registry,limits=limits,generation_constraints=constraints)
        validate_compiled(agent,Config());compiled.append(dict(candidate=directory.name,tools=len(agent.tools),sub_agents=len(agent.sub_agents)))
    canary=output/'owned_canary';canary.write_text('SYNTHETIC_PRIVATE_ONLY')
    fd=__import__('os').open(canary,0);__import__('os').set_inheritable(fd,True)
    manager=SubprocessManager(journal=Journal(output),base_dir=output/'roots',task_wheels=find_data()/'wheels')
    try:
        sid=manager.start()
        result=manager.exec(sid,'python3 -c '+shlex.quote(CANARY.replace('TARGETS',repr([str(canary)]))),timeout=120)
        atomic_json(output/'CANARY_RESULT.json',dict(exit_code=result.exit_code,stdout=result.stdout,stderr=result.stderr))
        assert result.exit_code==0 and 'INTEGRATED_CANARY_AND_DEPENDENCIES_OK' in result.stdout
        command="mkdir fastapi && printf 'VALUE=1\n' > fastapi/owned.py && git init -q && git config user.email owned@example.invalid && git config user.name Owned && git add . && git commit -qm original && git tag _swegemma_baseline && printf 'VALUE=2\n' > fastapi/owned.py"
        result=manager.exec(sid,command,timeout=120);assert result.exit_code==0,(result.stdout,result.stderr)
        command="printf 'VALUE=3\n' > fastapi/owned.py"
        result=manager.exec(sid,command,timeout=120);assert result.exit_code==0
    finally:__import__('os').close(fd);manager.cleanup_all()
    events=[json.loads(x) for x in (output/'events.jsonl').read_bytes().splitlines()]
    assert any(e.get('kind')=='source_boundary_observation' and 'fastapi/owned.py' in e['production_changed'] for e in events)
    atomic_json(output/'REPAIR_ACCEPTANCE.json',dict(status='CPU_PACKAGE_PREFLIGHT_REPAIR_PASS',all_frozen_source_pins_present=True,
        original_verifier_hashes_match=True,official_Compiler=compiled,accepted_runtime_fingerprint=True,
        actual_chroot_canary=True,passive_source_observer=True,cleanup=not manager.sandboxes,
        actual_Agent_runs=0,Gemma_calls=0,GPU=False,native_task_baselines=0,
        limitation='CPU package/Compiler/boundary repair evidence only;no GPU retry,model load or ABBA result'))
    print('CPU_PACKAGE_PREFLIGHT_REPAIR_PASS')

if __name__=='__main__':run(sys.argv[1])
