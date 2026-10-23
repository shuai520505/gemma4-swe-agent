"""Unchanged production worker plus passive Compiler/Prompt evidence only."""
import asyncio,json,sys
from pathlib import Path
from unittest.mock import patch
from .common import sha
from harness_v2.evidence import atomic_json,read_events

async def evaluate(spec,directory):
    import adk_submission
    from u_re.v01.experiments.action_priority_01.real_gemma_abba03 import worker as accepted
    source=Path(spec['agent_dir']);expected=(source/'prompts/system.md').read_text(encoding='utf8');observed=[]
    original=adk_submission.compile_submission
    def compile_observer(*args,**kwargs):
        agent=original(*args,**kwargs)
        assert agent.instruction==expected
        assert not agent.sub_agents and len(agent.tools)==6
        generation=agent.generate_content_config.model_dump(mode='json',exclude_none=True)
        assert generation==dict(max_output_tokens=16384,seed=17,thinking_config=dict(thinking_budget=4096))
        observed.append(dict(instruction_sha256=sha(agent.instruction.encode()),generation=generation,tools=sorted(getattr(t,'__name__',getattr(t,'name',None)) for t in agent.tools),agent_class=type(agent).__name__))
        return agent
    with patch.object(adk_submission,'compile_submission',compile_observer):await accepted.evaluate(spec,directory)
    requests=[e['body'] for e in read_events(Path(directory)/'agent/http_wire.jsonl') if e.get('kind')=='http_request']
    assert requests and observed
    for body in requests:
        system='\n'.join(m['content'] for m in body['messages'] if m.get('role')=='system')
        assert expected.strip() in system,'Compiled Prompt missing in actual model request'
        assert body.get('max_completion_tokens',body.get('max_tokens'))==16384 and body['thinking_token_budget']==4096 and body['seed']==17
    declarations=[sha(json.dumps(b['tools'],sort_keys=True).encode()) for b in requests]
    assert len(set(declarations))==1
    atomic_json(Path(directory)/'COMPILED_PROMPT_EVIDENCE.json',dict(candidate_sha256=spec['candidate_sha256'],instruction_sha256=sha(expected.encode()),compiled=observed,actual_HTTP_requests=len(requests),instruction_visible_in_all_actual_HTTP_requests=True,tools_schema_sha256=declarations[0],generation_unchanged=True,passive_observer=True))

if __name__=='__main__':
    d=Path(sys.argv[2]);d.mkdir(parents=True,exist_ok=True)
    try:asyncio.run(evaluate(json.loads(Path(sys.argv[1]).read_bytes()),d))
    except BaseException as exc:
        import traceback
        atomic_json(d/'worker_exception.json',dict(type=type(exc).__name__,error=str(exc),traceback=traceback.format_exc()));raise
