import inspect
import json
from pathlib import Path
import sys

from .common import ORDER,ROOT,package,config,write
from .data import prepare
from .evaluate import evaluate

def run(out):
    import torch
    from swegemma.config import EvalConfig
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    result=dict(GPU_devices=torch.cuda.device_count(),Gemma_requests=0,baselines={},configurations={},passed=False)
    assert result['GPU_devices']==0
    write(out/'EVAL_CONFIG_API.json',dict(signature=str(inspect.signature(EvalConfig)),source=inspect.getsource(EvalConfig)))
    print('EVAL_CONFIG_SIGNATURE',str(inspect.signature(EvalConfig)),flush=True)
    try:
        data=prepare(out/'data')
        for ident,binding in data.items():
            row=evaluate(binding,out/'baseline'/ident)
            result['baselines'][ident]=row
            print('BASELINE_RESULT',ident,json.dumps({k:row.get(k) for k in ('target_failed','positive_controls_passed','cleanup','execution')}),flush=True)
            assert row['target_failed'] and row['positive_controls_passed'] and row['cleanup'],ident
        for name in ('S0','SUPERAGENT'):
            candidate=out/'candidates'/name
            reg,limits,constraints,agent,budget=package(name,candidate,'/NO_MODEL_CPU_COMPILE_ONLY')
            binding=next(iter(data.values()))
            cfg=config(candidate,reg,limits,constraints,budget,binding['taskfile'],binding['snapshot'],binding['wheels'],out/name)
            result['configurations'][name]=dict(passed=True,budget=budget,actual_budget=str(cfg.budget),
                tools=[t.__name__ for t in agent.tools],generation=agent.generate_content_config.model_dump(mode='json',exclude_none=True),
                actual_turns=cfg.budget.turns,context_compaction=str(cfg.events_compaction_config))
        result['passed']=len(result['baselines'])==3 and len(result['configurations'])==2
    finally:write(out/'CPU_RESULTS.json',result)
    print('PAIRED_CPU_RESULTS',json.dumps(result),flush=True)
    assert result['passed']

if __name__=='__main__':run(sys.argv[1])
