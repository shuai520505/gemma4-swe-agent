"""Build a minimal GPU development Notebook only after a real CPU gate passes."""
import argparse
import ast
import hashlib
import inspect
import json
from pathlib import Path

from experiments.prepare import ROOT,write_new
from scripts.build_kaggle_notebook import INSTALL,SERVER
from notebooks import kaggle_support
from .batch import require_cpu_gate
from .build import cell
from .integrity import verify_baseline


def build(revision,gate_path):
    verify_baseline()
    plan=json.loads((ROOT/'harness_v2/registrations'/f'{revision}.json').read_text())
    gate=require_cpu_gate(gate_path,plan,ROOT)
    base=ROOT/'artifacts/harness-v2'/revision
    cpu=json.loads((base/'cpu-kernel/cpu.ipynb').read_text())
    setup=cpu['cells'][1]['source'].replace('harness_v2_cpu','harness_v2_gpu').replace('CPU infrastructure only','GPU infrastructure development only')
    setup+='\nSESSION_STARTED=time.monotonic()\nsys.path.insert(0,str(SOURCE))\n'
    setup+=f'CPU_GATE={gate!r}\nCPU_PLAN={plan!r}\n'
    setup+='''from harness_v2.evidence import atomic_json,bundle
from harness_v2.batch import require_cpu_gate,run_batch
bundle_run=bundle  # Organizer INSTALL/SERVER diagnostic branches use this name.
atomic_json(RUN_DIR/'cpu_gate.json',CPU_GATE)
require_cpu_gate(RUN_DIR/'cpu_gate.json',CPU_PLAN,SOURCE)
MODEL_NAME='gemma-4-31b-it-qat-w4a16-ct'
PLAN=plan
server_instance=None
profile=dict(task_wall_minutes=25.5,max_tasks=2)
'''
    helpers='''import logging,traceback
'''
    helpers+='\n'.join(inspect.getsource(getattr(kaggle_support,n)) for n in
        ('write_json','one_path','exception_record','preserve_server_log'))
    helpers+='''
def admission_seconds(started,minutes):
    return minutes*60 if 10800-(time.monotonic()-started)>=minutes*60+900 else 0
input_root=Path('/kaggle/input')
DATA_DIR=one_path([p.parent for p in input_root.rglob('tasks.jsonl') if (p.parent/'snapshots').is_dir()],'official tasks')
WHEELHOUSE_DIR=one_path([p.parent for p in input_root.rglob('swegemma-0.2.11-py3-none-any.whl')],'official wheels')
MODEL_PATH=one_path([p.parent for p in input_root.rglob('config.json') if MODEL_NAME in p.parts and any(p.parent.glob('*.safetensors'))],'required 31B v2')
AGENT_DIR=SOURCE/'candidates/v0/submission'
'''
    preflight='''import torch
from adk_submission import VllmConfig,VllmServer,compile_submission,discover_adapters
from swegemma.config import build_submission_limits
from swegemma.context import SwegemmaContext
assert torch.cuda.is_available() and torch.cuda.device_count()==4,'Official 4xL4 GPU required'
tp_size=4
adapters=discover_adapters(str(AGENT_DIR)); assert not adapters.adapters
limits,constraints=build_submission_limits()
assert constraints.defaults['max_output_tokens']==16384
'''
    run='''from harness_v2.context_budget import RequestGuard,VllmCounter,ContextBudgetExceeded
from google.adk.models.lite_llm import LiteLLMClient
from harness_v2.budgets import Budgets
try:
    counter=VllmCounter(server_instance.base_url,key)
    admissions=[]
    backend=LiteLLMClient()
    guard=RequestGuard(counter,backend.acompletion,core_issue='Infrastructure probe: reply OK.',emit=admissions.append)
    response=await guard.acompletion(model='openai/'+str(MODEL_PATH),api_base=server_instance.base_url,api_key=key,
        messages=[{'role':'user','content':'Infrastructure probe: reply OK.'}],tools=None,max_completion_tokens=8,
        extra_body={'chat_template_kwargs':{'enable_thinking':False}})
    probe=dict(kind='infrastructure_probe_not_task_repair',actual_model=response.model,
        generated_tokens=response.usage.completion_tokens,input_tokens=response.usage.prompt_tokens,
        tokenizer_input_tokens=admissions[-1]['input_tokens'],admission=admissions[-1])
    assert probe['generated_tokens']>0
    assert str(MODEL_PATH) in probe['actual_model']
    assert probe['input_tokens']==probe['tokenizer_input_tokens'],'Tokenizer/rendering mismatch; stop before task runs'
    async def forbidden_generation(**kwargs):
        raise AssertionError('Oversize request reached generation')
    oversized=[]
    guard=RequestGuard(counter,forbidden_generation,core_issue='Boundary probe',emit=oversized.append)
    try:
        await guard.acompletion(model='openai/'+str(MODEL_PATH),messages=[{'role':'user','content':' token'*20000}],
            tools=None,max_completion_tokens=16384)
    except ContextBudgetExceeded:
        probe['oversize_rejected_before_generation']=True
        probe['oversize_admission']=oversized[-1]
    else:
        raise AssertionError('Oversize probe was not rejected')
    atomic_json(RUN_DIR/'gpu_probe.json',probe)
    paths=dict(tasks_path=str(DATA_DIR/'tasks.jsonl'),snapshots_dir=str(DATA_DIR/'snapshots'),
        wheels_dir=str(DATA_DIR/'wheels'),graph_dir=str(DATA_DIR/'graphs'),embeddings_dir=str(DATA_DIR/'embeddings'))
    model=dict(model_path=str(MODEL_PATH),model_alias=MODEL_NAME,base_url=server_instance.base_url)
    records=run_batch(PLAN,SOURCE,RUN_DIR/'runs',paths,model,session_started=SESSION_STARTED)
except BaseException as exc:
    exception_record(RUN_DIR,'gpu_infrastructure',exc)
    raise
finally:
    preserve_server_log(server_instance,RUN_DIR)
    server_instance.stop()
    handler.flush(); handler.close()
    print('GPU EVIDENCE ZIP',bundle(RUN_DIR),flush=True)
'''
    nb=dict(cells=[dict(cell_type='markdown',metadata={},source='# Harness V2 minimal GPU development smoke\nCPU gate passed before building. Two preassigned development tasks; no formal V0/V1 comparison.'),
        cell(setup),cell(helpers),cell(INSTALL),cell(preflight),cell(SERVER),cell(run)],
        metadata=dict(kernelspec=dict(display_name='Python 3',language='python',name='python3')),nbformat=4,nbformat_minor=5)
    # Stable cell IDs avoid nbformat repair warnings in the saved execution.
    for c in nb['cells']: c['id']=hashlib.sha256(c['source'].encode()).hexdigest()[:12]
    data=(json.dumps(nb,indent=1)+'\n').encode()
    write_new(base/'gpu-kernel/gpu.ipynb',data)
    meta=json.loads((ROOT/'artifacts/v1-pilot/kernel/kernel-metadata.json').read_text())
    meta.update(id='wudangdexiaodoashi/gemma4-harness-v2-gpu-smoke',title='Gemma4 Harness V2 GPU Smoke',
        code_file='gpu.ipynb',dataset_sources=['metric/gemma-4-developer-agent-wheelhouse',
        'wudangdexiaodoashi/gemma4-harness-v2-private-input'])
    write_new(base/'gpu-kernel/kernel-metadata.json',(json.dumps(meta,indent=2)+'\n').encode())
    registration=dict(experiment_id=plan['experiment_id'],revision=revision,kind='gpu_development_smoke',
        cpu_gate_sha256=hashlib.sha256(Path(gate_path).read_bytes()).hexdigest(),
        cpu_plan_sha256=hashlib.sha256((ROOT/'harness_v2/registrations'/f'{revision}.json').read_bytes()).hexdigest(),
        notebook_sha256=hashlib.sha256(data).hexdigest(),tasks=plan['tasks'],
        source_hashes=plan['source_hashes'],gpu_status_at_registration='not_executed',competition_score=None)
    write_new(ROOT/'harness_v2/registrations'/f'{revision}-gpu.json',(json.dumps(registration,indent=2)+'\n').encode())
    print(json.dumps(dict(notebook=str(base/'gpu-kernel/gpu.ipynb'),sha256=registration['notebook_sha256'],
        cpu_gate_passed=True,gpu_executed=False),indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('revision'); p.add_argument('cpu_gate',type=Path)
    a=p.parse_args(); build(a.revision,a.cpu_gate)
