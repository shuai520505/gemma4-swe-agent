"""Invoke the pinned real organizer compiler; never invoke model.generate_content."""
import os,json,hashlib,traceback,sys,zipfile
from pathlib import Path
import importlib.metadata as md

os.environ.update(LITELLM_LOCAL_MODEL_COST_MAP='True',LITELLM_TELEMETRY='False',OTEL_SDK_DISABLED='true')
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
result=dict(evidence='CPU_VERIFIED',real_Gemma_requests=0,model_loaded=False,compiler='adk_submission.compile_submission; unmodified official tool registry',status='NOT_RUN')
try:
 from adk_submission import ModelRegistry,compile_submission,validate_directory
 from google.adk.models.lite_llm import LiteLlm
 from swegemma.config import build_submission_limits,EvalConfig
 from swegemma.context import SwegemmaContext
 result['versions']={n:md.version(n) for n in ('swegemma','adk-submission','adk-eval-core','google-adk','google-genai','litellm')}
 assert result['versions']=={'swegemma':'0.2.11','adk-submission':'0.2.13','adk-eval-core':'0.1.0','google-adk':'1.36.1','google-genai':'2.11.0','litellm':'1.82.4'}
 registry=ModelRegistry();label='gemma-4-31b-it-qat-w4a16-ct'
 registry.register(label,LiteLlm(model='openai/'+label,api_base='http://127.0.0.1:9/v1',api_key='EMPTY'))
 limits,constraints=build_submission_limits();context=SwegemmaContext();tools=context.create_tools()
 folder=OUT/'submission_r2_candidate';validate_directory(folder,limits=limits)
 agent=compile_submission(folder,tools,registry,limits=limits,generation_constraints=constraints)
 import yaml
 flat=yaml.safe_load((folder/'eval_config.yaml').read_text())['evaluation']
 config=EvalConfig(tasks_path=OUT/'unused-tasks',snapshots_dir=OUT/'unused-snapshots',results_dir=OUT/'unused-results',submission_dir=folder,models=registry,**flat)
 result.update(status='PASS',instruction_sha256=hashlib.sha256(agent.instruction.encode()).hexdigest(),tools=[t.__name__ for t in agent.tools],generation=agent.generate_content_config.model_dump(mode='json',exclude_none=True),budget=str(config.budget),command_timeout_seconds=config.harness.command_timeout_seconds,verification_timeout_seconds=config.harness.verification_timeout_seconds)
 assert config.budget.time_minutes==8 and config.budget.tool_calls==28 and config.budget.turns==80 and config.harness.command_timeout_seconds==240
 assert not agent.sub_agents
 for name in ('adk_submission/compiler.py','swegemma/config.py','swegemma/context.py','swegemma/tools/execution.py'):
  dist=md.distribution(name.split('/')[0].replace('_','-'));path=Path(dist.locate_file(name));result.setdefault('official_source_sha256',{})[name]=hashlib.sha256(path.read_bytes()).hexdigest()
except BaseException as e:result.update(status='FAILED',error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc())
(OUT/'CPU_COMPILER_RESULT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print(json.dumps(result));raise SystemExit(result['status']!='PASS')
