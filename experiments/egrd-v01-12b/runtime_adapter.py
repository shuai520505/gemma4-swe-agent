"""Research host binding; portable EGRD itself remains inside official Skill."""
import io,json,zipfile
from pathlib import Path
from adk_submission import ModelRegistry,compile_submission,validate_directory
from google.adk.models.lite_llm import LiteLlm
from swegemma.context import SwegemmaContext
from swegemma.config import build_submission_limits
import r2a_runtime
HERE=Path(__file__).resolve().parent
def package(name,out,model_path='CPU_ONLY_NO_REQUESTS'):
    if name=='R2':name='A' # No inference occurs in independent verification.
    manifest=json.loads((HERE/'PACKAGE_MANIFEST.json').read_bytes())['arms'][name]
    raw=(HERE/'packages'/f'{name}.zip').read_bytes();assert r2a_runtime.sha(raw)==manifest['sha256']
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        assert z.testzip() is None and all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in z.namelist());z.extractall(out)
    registry=ModelRegistry();registry.register(manifest['model'],LiteLlm(model='openai/'+model_path,api_base='http://127.0.0.1:8000/v1',api_key='EMPTY'))
    limits,constraints=build_submission_limits();validate_directory(out,limits=limits)
    agent=compile_submission(out,SwegemmaContext().create_tools(),registry,limits=limits,generation_constraints=constraints)
    return registry,limits,constraints,agent,dict(timeout_seconds=120,max_tool_calls=60,max_time_minutes=5,max_turns=80)
def install():
    r2a_runtime.package=package
    from hardened_runtime import SubprocessManager
    r2a_runtime.SubprocessManager=SubprocessManager
