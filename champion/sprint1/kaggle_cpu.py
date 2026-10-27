"""Private Kaggle CPU: original patch checks and actual official compilation."""
import importlib.metadata as md
import json
from pathlib import Path
import sys
import traceback
import zipfile
from .build import ROOT,HERE,S0_SHA,NAMES,base,archive,sha,write

def run(output):
    from adk_submission import ModelRegistry,compile_submission,validate_directory
    from google.adk.models.lite_llm import LiteLlm
    from swegemma.config import build_submission_limits
    from swegemma.context import SwegemmaContext
    from egrd.v032.data import prepare
    from egrd.v032.evaluate import evaluate
    import torch
    out=Path(output);out.mkdir(parents=True,exist_ok=False)
    result=dict(GPU_devices=torch.cuda.device_count(),Gemma_requests=0,model_loading=False,Notebook_dispatches=1,
        SDK={n:md.version(n) for n in ('swegemma','adk-submission','google-adk','adk-eval-core')},
        compilers={},patch_evaluations={},CPU_MODEL='NO_MODEL_COMPILER_AND_OWNED_TESTS_ONLY')
    assert result['GPU_devices']==0
    pins=json.loads((ROOT/'egrd/v023/RECOVERED_DEPENDENCY_IDENTITIES.json').read_bytes())
    assert result['SDK']==pins['SDK']
    for name,h in pins['installed_official_source_hashes'].items():
        dist=md.distribution('google-adk' if name.startswith('google/') else name.split('/')[0].replace('_','-'))
        assert sha(Path(dist.locate_file(name)).read_bytes())==h,name
    original=base();assert sha((ROOT/'candidates/s0/submission.zip').read_bytes())==S0_SHA
    frozen=json.loads((HERE/'CANDIDATE_MANIFEST.json').read_bytes())['candidates']
    try:
        for name in ('S0',*NAMES):
            try:
                files=original.copy()
                if name=='C2_CONTEXT':files['agent.yaml']+=b'\ngenerate_content_config:\n  max_output_tokens: 8192\n'
                elif name!='S0':files['prompts/system.md']+=b'\n\n'+(HERE/(name+'.md')).read_bytes()
                if name!='S0':
                    raw=archive(files);assert sha(raw)==frozen[name]['sha256']
                    package=out/'candidates'/name/'submission.zip';package.parent.mkdir(parents=True);package.write_bytes(raw)
                    assert archive(files)==raw
                else:raw=(ROOT/'candidates/s0/submission.zip').read_bytes()
                import io
                folder=out/'compiled'/name
                with zipfile.ZipFile(io.BytesIO(raw)) as z:
                    assert z.testzip() is None and set(z.namelist())==set(original)
                    z.extractall(folder)
                label='gemma-4-31b-it-qat-w4a16-ct';registry=ModelRegistry()
                registry.register(label,LiteLlm(model='openai/'+label,api_base='http://127.0.0.1:9/v1',api_key='EMPTY'))
                limits,constraints=build_submission_limits();validate_directory(folder,limits=limits)
                agent=compile_submission(folder,SwegemmaContext().create_tools(),registry,limits=limits,generation_constraints=constraints)
                gen=agent.generate_content_config.model_dump(mode='json',exclude_none=True)
                assert gen=={'max_output_tokens':8192 if name=='C2_CONTEXT' else 16384,'thinking_config':{'thinking_budget':4096}}
                assert agent.instruction==(folder/'prompts/system.md').read_text()
                tools=[t.__name__ for t in agent.tools]
                assert tools==['get_status','run_command','read_file','edit_file','write_file','submit_patch'] and not agent.sub_agents
                changed=[n for n in sorted(files) if files[n]!=original[n]]
                assert changed==([] if name=='S0' else ['agent.yaml'] if name=='C2_CONTEXT' else ['prompts/system.md'])
                result['compilers'][name]=dict(status='FULL_COMPILER_PASS',sha256=sha(raw),generation=gen,tools=tools,
                    instruction_sha256=sha(agent.instruction.encode()),changed_members=changed,
                    deterministic_rebuild=True,model_label=label,model_requests=0)
            except Exception as e:
                result['compilers'][name]=dict(status='COMPILER_BLOCKED',error_type=type(e).__name__,error=str(e))
                write(out/('compiler_'+name+'_error.json'),dict(traceback=traceback.format_exc()))
        data=prepare(out/'data')
        patch=(HERE/'private/original_fallback.patch').read_bytes()
        assert sha(patch)=='d0aba874e19c5c109f39f870c005e80666d1a0a091b0f8e0a428d6c6865bf838'
        production=b''.join(b'diff --git '+p for p in patch.split(b'diff --git ')[1:] if p.startswith(b'a/django/'))
        assert production and production!=patch
        (out/'production_only_DERIVED.patch').write_bytes(production)
        result['original_patch_sha256']=sha(patch);result['production_only_patch_sha256']=sha(production)
        for name,body in [('original_base',None),('original_fallback',patch),('production_only_DERIVED',production)]:
            try:
                row=evaluate(data['task'],Path(data['data']),out/name,Path(data['snapshot']),Path(data['wheels']),
                    Path(data['regression']),body.decode() if body else None)
                result['patch_evaluations'][name]=row
            except Exception as e:
                result['patch_evaluations'][name]=dict(classification='ENVIRONMENT_BLOCKED',error_type=type(e).__name__,error=str(e))
                write(out/(name+'_ERROR.json'),dict(traceback=traceback.format_exc()))
        result['S0_unchanged']=sha((ROOT/'candidates/s0/submission.zip').read_bytes())==S0_SHA
        result['compiled_all']=len(result['compilers'])==4 and all(r['status']=='FULL_COMPILER_PASS' for r in result['compilers'].values())
        result['official_native_resolved']=None;result['canonical_swebench_resolved']=None
    finally:write(out/'CPU_RESULTS.json',result)
    print(json.dumps({k:result[k] for k in ('compiled_all','GPU_devices','Gemma_requests','S0_unchanged')}),flush=True)

if __name__=='__main__':run(sys.argv[1])
