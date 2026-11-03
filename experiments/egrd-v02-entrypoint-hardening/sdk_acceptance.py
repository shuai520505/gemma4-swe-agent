"""Real frozen official Compiler; no model invocation or simulated imports."""
import asyncio,hashlib,importlib.metadata,json,shutil,tempfile
from pathlib import Path
from adk_submission import ModelRegistry,compile_submission,validate_directory
from google.adk.models.lite_llm import LiteLlm
from swegemma.context import SwegemmaContext
from swegemma.config import build_submission_limits
D=Path(__file__).resolve().parent
async def main():
    manifest=json.loads((D/'PACKAGE_MANIFEST.json').read_bytes());rows=[];tool_schemas={}
    limits,constraints=build_submission_limits()
    for arm in ['A','B','C','D']:
        package=D/'packages'/arm;alias=manifest['arms'][arm]['model'];registry=ModelRegistry()
        registry.register(alias,LiteLlm(model='openai/'+alias,api_base='http://127.0.0.1:8000/v1',api_key='EMPTY'))
        validate_directory(package,limits=limits)
        agent=compile_submission(package,SwegemmaContext().create_tools(),registry,limits=limits,generation_constraints=constraints)
        assert type(agent).__name__=='LlmAgent' and not agent.sub_agents
        direct=[t.__name__ for t in agent.tools if hasattr(t,'__name__')]
        skill=[t for t in agent.tools if type(t).__name__=='SkillToolset'];assert len(skill)==1
        actual_tools=await skill[0].get_tools();accessors=[t.name for t in actual_tools]
        for t in actual_tools:tool_schemas[t.name]=t._get_declaration().model_dump(mode='json',exclude_none=True)
        assert set(direct)==set(manifest['base_tools'])
        assert set(accessors)==set(manifest['official_skill_accessors'])
        rows.append(dict(arm=arm,model=alias,agent_count=1,base_tools=direct,official_skill_accessors=accessors,generation=agent.generate_content_config.model_dump(mode='json',exclude_none=True),instruction_sha256=hashlib.sha256(agent.instruction.encode()).hexdigest(),callbacks_active=bool(agent.before_tool_callback)))
    assert rows[0]['generation']==rows[1]['generation']==rows[2]['generation']==rows[3]['generation']
    assert len(set(r['instruction_sha256'] for r in rows))==1
    with tempfile.TemporaryDirectory() as tmp:
        probe=Path(tmp)/'package';shutil.copytree(D/'packages/D',probe)
        with (probe/'agent.yaml').open('a') as f:f.write('\nbefore_tool_callbacks: [egrd_gate_not_registered]\n')
        a=compile_submission(probe,SwegemmaContext().create_tools(),registry,limits=limits,generation_constraints=constraints)
        assert not a.before_tool_callback
    for n,required in [('load_skill',{'skill_name'}),('run_skill_script',{'skill_name','file_path'})]:
        schema=tool_schemas[n]['parameters_json_schema'];assert required<=set(schema['required'])
    (D/'evidence/SDK_TOOL_SCHEMAS.json').write_text(json.dumps(tool_schemas,indent=2)+'\n')
    result=dict(status='CPU_COMPILER_PASS',rows=rows,callback_probe='YAML callback names are inactive when organizer passes no CallbackRegistry; no custom global controller',versions={p:importlib.metadata.version(p) for p in ['adk-submission','swegemma','google-adk','google-genai']},real_model_requests=0,model_tool_calling='NOT_RUN',skill_executor='MUST_VERIFY_THROUGH_REAL_SANDBOX_SEPARATELY')
    (D/'evidence/SDK_COMPILER.json').write_text(json.dumps(result,indent=2)+'\n');print('CPU_COMPILER_PASS')
if __name__=='__main__':asyncio.run(main())
