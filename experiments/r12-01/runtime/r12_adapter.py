"""Thin binding of frozen R12 inputs to PR43's worker; no new Agent controller."""
import asyncio,hashlib,json,sys,zipfile,time
from pathlib import Path
from unittest.mock import patch
from env_runtime_repair import repair
from r12_preflight import SubprocessManager as ProjectManager,add_dependencies

HERE=Path(__file__).parent
HASHES={'BASELINE':'944e1d23ce5e93a77af3e993834487e829487aff0a92ec7fe3e115590bfaf9f1','R1':'c0cd26d1084a8a480689db57012e0b0900a33c5fb9951b38aa0101a456c8f2a1','R2':'af918c1a65aeb211298f13a69b5b789ae6b086974922c80469df87d902eb98d5'}

def package(name,destination,model_path):
    from adk_submission import ModelRegistry,validate_directory,compile_submission
    from google.adk.models.lite_llm import LiteLlm
    from swegemma.config import build_submission_limits
    from swegemma.context import SwegemmaContext
    import yaml
    raw=(HERE/'candidates'/(name+'.zip')).read_bytes();assert hashlib.sha256(raw).hexdigest()==HASHES[name]
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=False)
    import io
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        assert z.testzip() is None and set(z.namelist())=={'agent.yaml','eval_config.yaml','configs/sampling.yaml','prompts/system.md'}
        z.extractall(destination)
    budget=yaml.safe_load((destination/'eval_config.yaml').read_text())['evaluation']
    assert budget==dict(timeout_seconds=240,max_tool_calls=28,max_time_minutes=8,max_turns=80)
    registry=ModelRegistry();registry.register('gemma-4-31b-it-qat-w4a16-ct',LiteLlm(model='openai/'+model_path,api_base='http://127.0.0.1:8000/v1',api_key='EMPTY'))
    limits,constraints=build_submission_limits();validate_directory(destination,limits=limits)
    compiled=compile_submission(destination,SwegemmaContext().create_tools(),registry,limits=limits,generation_constraints=constraints)
    assert not compiled.sub_agents
    return registry,limits,constraints,compiled,budget

def bind_manager(binding):
    """Same CPU-verified project environment for Agent and fresh verifier roots."""
    legacy=binding['issue']['instance_id'].startswith('pytest')
    class SubprocessManager(ProjectManager):
        def _process(self,sid,mode,argument,data=None,timeout=None):
            before=time.monotonic()
            result=super()._process(sid,mode,argument,data=data,timeout=timeout)
            context=getattr(self,'context',None)
            if context is None or context.agent_start_time is None or context.agent_end_time is not None:return result
            workspace=self.sandboxes[sid]['workspace'];changes=[]
            for name,expected in binding.get('production_files',{}).items():
                if Path(name).name in ('conftest.py','setup.py'):continue
                path=workspace/name
                if path.exists() and path.resolve().is_relative_to(workspace.resolve()) and path.is_file():
                    if hashlib.sha256(path.read_bytes()).hexdigest()!=expected:changes.append(name)
            if changes and not getattr(self,'first_edit_recorded',False):
                self.first_edit_recorded=True
                self.journal.append(dict(kind='first_production_edit_observed',observed_monotonic=time.monotonic(),lower_bound_monotonic=before,changed_files=changes,timing='First completed confined operation observing changed production bytes; interval, not exact write instant'))
            return result
        def __init__(self,*args,**kwargs):
            base=Path(kwargs['base_dir'])
            kwargs['base_dir']=base if base.name=='roots' else base/'roots'
            super().__init__(*args,legacy_project=legacy,**kwargs)
        def start(self):
            sid=super().start()
            try:
                root=self.sandboxes[sid]['root'];repair(root)
                extras=[Path(p) for p in binding.get('runtime_extra_wheels',[])]
                expected=binding.get('runtime_extra_sha256',{})
                assert all(hashlib.sha256(p.read_bytes()).hexdigest()==expected[p.name] for p in extras)
                add_dependencies(root,extras,legacy)
                if legacy:
                    script=root/'usr/local/bin/pytest';script.write_text('#!/usr/bin/python3\nfrom pytest import main\nraise SystemExit(main())\n');script.chmod(0o755)
                return sid
            except BaseException:self.stop(sid);raise
    return SubprocessManager

async def run(spec,out):
    # This turn creates no authorization receipt, server, or GPU Notebook.
    if spec.get('CPU_simulation') is True:
        import torch
        assert torch.cuda.device_count()==0 and spec['model_path']=='SIMULATED_CPU_NO_MODEL'
    elif spec.get('new_explicit_GPU_authorization') is not True:raise PermissionError('New explicit user GPU authorization is required')
    import gemma_pair.worker as worker
    import gemma_pair.evaluate as evaluator
    manager=bind_manager(spec['binding'])
    with patch.object(worker,'package',package),patch.object(worker,'SubprocessManager',manager),patch.object(evaluator,'SubprocessManager',manager):
        await worker.run(spec,out)
    from r12_evidence import finalize
    finalize(out)

def trusted_binding(binding,program_directory):
    """Bind existing, byte-identical checks; never invoked by CPU plumbing replay."""
    root=Path(program_directory);ident=binding['issue']['instance_id']
    names=['probe.py','pytest.ini','test_assertion_canary.py','test_array_patch.py','test_controls.py']
    binding=dict(binding,evaluation_programs={n:str(root/n) for n in names},
        evaluation_command='PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python /evaluation/probe.py '+ident,
        evaluation_receipt='/tmp/r12-receipt.json')
    assert hashlib.sha256((root/'probe.py').read_bytes()).hexdigest()=='b46f783792cb6c2019f2af50279dcff123828f806b0542babf2836bcc92bb667'
    return binding

if __name__=='__main__':asyncio.run(run(json.loads(Path(sys.argv[1]).read_bytes()),sys.argv[2]))
