"""CPU-only official Compiler check of immutable S0 and V0.2 D.
Public generation_constraints supplies common defaults, without editing ZIPs.
This proves compile-time feasibility, not model or Linux acceptance.
"""
import asyncio, dataclasses, hashlib, importlib.metadata, json, tempfile, zipfile
from pathlib import Path
from adk_submission import ModelRegistry, compile_submission, validate_directory
from google.adk.models.lite_llm import LiteLlm
from swegemma.context import SwegemmaContext
from swegemma.config import build_submission_limits

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
async def main():
    limits,original=build_submission_limits()
    common={'max_output_tokens':8192,'temperature':0.2,'top_p':0.95,'thinking_config':{'thinking_budget':4096,'include_thoughts':True}}
    constraints=dataclasses.replace(original,defaults=common)
    registry=ModelRegistry();alias='gemma-4-31b-it-qat-w4a16-ct'
    registry.register(alias,LiteLlm(model='openai/'+alias,api_base='http://127.0.0.1:1/v1',api_key='EMPTY'))
    rows=[]
    with tempfile.TemporaryDirectory() as temp:
        for arm,path in [('S0',ROOT/'outputs/verified_candidates/S0.zip'),('EGRD_V02_D',ROOT/'experiments/egrd-v02-entrypoint-hardening/packages/D.zip')]:
            b=path.read_bytes(); folder=Path(temp)/arm;folder.mkdir()
            with zipfile.ZipFile(path) as z:
                assert all(not n.startswith(('/','\\')) and '..' not in Path(n).parts for n in z.namelist())
                z.extractall(folder)
            validate_directory(folder,limits=limits)
            for mode,c in [('official_defaults',original),('common_public_defaults',constraints)]:
                agent=compile_submission(folder,SwegemmaContext().create_tools(),registry,limits=limits,generation_constraints=c)
                access=[]
                for t in agent.tools:
                    if type(t).__name__=='SkillToolset':access.extend(x.name for x in await t.get_tools())
                rows.append({'arm':arm,'mode':mode,'zip_sha256':hashlib.sha256(b).hexdigest(),'instruction_sha256':hashlib.sha256(agent.instruction.encode()).hexdigest(),'generation':agent.generate_content_config.model_dump(mode='json',exclude_none=True),'base_tools':[t.__name__ for t in agent.tools if hasattr(t,'__name__')],'skill_accessors':access,'before_tool_callback_active':bool(agent.before_tool_callback),'sub_agents':len(agent.sub_agents)})
    same=[r for r in rows if r['mode']=='common_public_defaults']
    assert same[0]['generation']==same[1]['generation']
    assert same[0]['base_tools']==same[1]['base_tools']
    result={'status':'CPU_COMPILER_PARITY_PASS','real_model_calls':0,'official_code_modified':False,'rows':rows,'versions':{p:importlib.metadata.version(p) for p in ['adk-submission','swegemma','google-adk','google-genai']},'limitation':'S0 package bytes unchanged; prospective common generation defaults differ from historical S0 defaults. Not a reproduction of historical serving settings. Linux Native trust gate remains blocked.'}
    (HERE/'CONFIGURATION_PARITY.json').write_text(json.dumps(result,indent=2)+'\n')
    print(result['status'])
if __name__=='__main__':asyncio.run(main())
