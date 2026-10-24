"""Targeted real official worker + shared Context Guard/Skill compatibility.

Executed only in a separate CPU payload. Never part of GPU execution imports.
"""
import asyncio
import hashlib
import json
from pathlib import Path
import sys


async def run(output):
    import torch
    from s1.task_identity import find_data
    from meer.v01.cpu_acceptance import actions, transport, write
    from .worker import evaluate
    assert torch.cuda.device_count() == 0
    output = Path(output); output.mkdir(parents=True, exist_ok=False)
    data = find_data(); records = []
    for arm in ('A','B','C'):
        base = output/arm; base.mkdir()
        t = transport(actions(arm)).start(data, base)
        directory = base/'worker'; directory.mkdir()
        try:
            spec = dict(execution_mode='CPU_VALIDATION', model_transport='CPU_SCRIPTED_ONLY',
                        instance_id='ure_gpu03_owned', arm=arm, agent_dir=str(Path(__file__).parents[1]/'candidates'/arm),
                        data=str(t.data), model_path=t.model_path, base_url=t.base_url, baseline_capture=str(t.baseline))
            await evaluate(spec, directory)
            native = json.loads((directory/'official_result.json').read_bytes())
            done = json.loads((directory/'worker_done.json').read_bytes())
            assert native['resolved'] is True and done['cleanup_complete'] and done['integrity_complete']
            cfg = json.loads((directory/'runtime_config.json').read_bytes())
            assert cfg['real_model'] is False and cfg['generation']==dict(max_output_tokens=16384,seed=17,thinking_config=dict(thinking_budget=4096))
            declarations = []
            for body in t.calls:
                assert body.get('max_completion_tokens',body.get('max_tokens'))==16384
                assert body['thinking_token_budget']==4096 and body['seed']==17
                declarations.append(sorted(x['function']['name'] for x in body['tools']))
            assert len(set(tuple(x) for x in declarations))==1
            assert len(declarations[0])==(6 if arm=='A' else 10)
            events = [json.loads(x) for x in (directory/'agent/adk_events.jsonl').read_bytes().splitlines()]
            responses = [p['function_response'] for e in events for p in e.get('event',{}).get('content',{}).get('parts',[]) if p.get('function_response')]
            results=[]
            for event in responses:
                if event['name']=='run_skill_script':
                    results.append(json.loads(event['response']['stdout']))
            if arm=='B':
                assert [v['verdict'] for v in results]==['CONTRADICTED','SUPPORTED','OBSERVED']
            elif arm=='C':
                assert len(results)==3 and all(v['verdict']=='UNKNOWN' for v in results)
            assert {'get_status','read_file','write_file','edit_file','run_command','submit_patch'} <= {e['name'] for e in responses}
            records.append(dict(arm=arm, CPU_MODEL='SCRIPTED_ONLY', real_Gemma_requests=0,
                official_worker=True, common_context_guard=True, actual_HTTP_requests=len(t.calls),
                schema=declarations[0], native_synthetic_resolved=native['resolved'],
                TaskResult_sha256=hashlib.sha256((directory/'official_result.json').read_bytes()).hexdigest(),
                JUnit_sha256=hashlib.sha256((directory/'verifier/phase2.junit.xml').read_bytes()).hexdigest(),
                patch_sha256=hashlib.sha256((directory/'final.patch').read_bytes()).hexdigest(),
                mechanism_verdicts=[v['verdict'] for v in results], cleanup_complete=True))
        finally:
            t.stop(); write(base/'TRANSPORT_CLEANUP.json',dict(complete=t.cleaned))
        assert t.cleaned
    write(output/'CPU_ACCEPTANCE.json',dict(status='MEER_GPU_WORKER_CPU_PASS',CPU_MODEL='SCRIPTED_ONLY',
          real_Gemma_requests=0, records=records, coordinator_GPU_runtime='NOT_RUN'))


if __name__=='__main__':
    asyncio.run(run(sys.argv[1]))
