"""Single source for compiled generation, actual HTTP cap and guard reservation."""
import asyncio,json
from pathlib import Path
from s1.config import Config
from s1.guard import Guard
from harness_v2.context_budget import ContextPolicy,ContextBudgetExceeded
POLICIES={'A':16384,'B':8192}
def budget(arm):return Config(output_tokens=POLICIES[arm])
def input_cap(arm):return 32768-budget(arm).output_tokens-1024

def research_candidate(original,destination,arm):
    """Trusted ephemeral configuration override; original candidate never edited."""
    import shutil,yaml
    original=Path(original);destination=Path(destination)
    assert not destination.exists()
    shutil.copytree(original,destination)
    path=destination/'agent.yaml';raw=path.read_bytes()
    assert raw.count(b'max_output_tokens: 16384')==1
    if arm=='B':path.write_bytes(raw.replace(b'max_output_tokens: 16384',b'max_output_tokens: 8192'))
    else:assert arm=='A'
    assert (original/'prompts/system.md').read_bytes()==(destination/'prompts/system.md').read_bytes()
    assert (original/'eval_config.yaml').read_bytes()==(destination/'eval_config.yaml').read_bytes()
    assert path.read_bytes().replace(b'max_output_tokens: 8192',b'max_output_tokens: 16384')==raw
    return destination

async def boundary_checks():
    """Actual Guard -> model communication boundary, no real model or task."""
    rows=[]
    for arm,values in [('A',[15360,15361]),('B',[15361,23552,23553])]:
        for count in values:
            sent=[];events=[]
            async def counter(body):return dict(count=count,max_model_len=32768)
            async def generate(**kw):sent.append(kw);return 'SCRIPTED_ONLY'
            c=budget(arm);guard=Guard(counter,generate,config=c,core_issue='OWNED',emit=events.append)
            rejected=False
            try:await guard.acompletion(model='openai/owned',messages=[dict(role='user',content='OWNED')],max_completion_tokens=c.output_tokens)
            except ContextBudgetExceeded:rejected=True
            assert rejected==(count>input_cap(arm))
            for request in sent:
                assert request['max_completion_tokens']==c.output_tokens
                assert request['extra_body']['thinking_token_budget']==4096 and request['seed']==17
            rows.append(dict(policy=arm,input=count,input_cap=input_cap(arm),rejected=rejected,generation_requests=len(sent),events=events))
    # Mismatched generation/guard is always rejected before dispatch.
    try:await Guard(counter,generate,config=budget('B'),core_issue='').acompletion(model='owned',messages=[],max_completion_tokens=16384)
    except ValueError:pass
    else:raise AssertionError('Mismatched cap accepted')
    return rows
