"""Independent disposable native verification and transparent follow-up diagnostics."""
import asyncio
import base64
import json
from pathlib import Path
import shlex
import time
from harness_v2.evidence import Journal,atomic_json
from s1.verifier_v3.environment import SubprocessManager as NativeManager,research_environment
from s1.verifier_v3.audit import audit_verifier


class SubprocessManager(NativeManager):
    def __init__(self,*args,variants=(),**kwargs):
        super().__init__(*args,**kwargs);self.variants=variants;self.diagnosed=set()

    def stop(self,sandbox_id):
        if sandbox_id in self.junit_paths and sandbox_id not in self.diagnosed:
            self.diagnosed.add(sandbox_id)
            code=Path(__file__).with_name('rich_probe.py').read_bytes()
            encoded=base64.b64encode(code).decode()
            for label,environment in self.variants:
                dest=(self.journal.directory/('diagnostic-'+label+'.json')).resolve()
                assignments=dict(EGV_DIAG_OUTPUT=str(dest),**environment)
                command='cd /workspace && '+ ' '.join(k+'='+shlex.quote(v) for k,v in assignments.items())+' python3 -s -c '+shlex.quote("exec(__import__('base64').b64decode("+repr(encoded)+"),{'__name__':'__main__'})")
                result=super().exec(sandbox_id,command,timeout=90)
                atomic_json(self.journal.directory/('diagnostic-'+label+'-execution.json'),dict(
                    exit_code=result.exit_code,stdout=result.stdout,stderr=result.stderr,diagnostic_only=True,native_Phase2_unchanged=True))
        return super().stop(sandbox_id)


async def run(output):
    from adk_submission import ModelRegistry
    from swegemma.models import load_tasks
    from swegemma.config import EvalConfig
    from swegemma.deduplication import resolve_task_snapshot_paths
    from swegemma.harness.verification import verify_task
    from s1.task_identity import find_data
    data=find_data();output=Path(output);task=next(t for t in load_tasks(data/'tasks.jsonl') if t.instance_id=='rich_3130')
    snapshot,base,overlay=resolve_task_snapshot_paths(data/'snapshots',task.instance_id,task.repo)
    for arm in ('baseline','control','e3'):
        dest=output/arm;dest.mkdir(parents=True,exist_ok=False)
        variants=[('original',{})]
        if arm=='baseline':variants += [('term_dumb',{'TERM':'dumb'}),('term_xterm',{'TERM':'xterm-256color'})]
        manager=SubprocessManager(journal=Journal(dest),base_dir=dest/'sandbox_tmp',audit_modules=['rich','pygments'],task_wheels=data/'wheels',variants=variants)
        manager.agent_id='independent_readonly_evaluator'
        cfg=EvalConfig(tasks_path=data/'tasks.jsonl',snapshots_dir=data/'snapshots',results_dir=dest/'native',submission_dir=Path('s1/candidates/control'),models=ModelRegistry(),sandbox='subprocess',wheels_dir=data/'wheels',verification_timeout_seconds=300,enable_sandbox_testing=True,display_mode='quiet')
        repair='' if arm=='baseline' else Path(__file__).with_name('fixtures').joinpath(arm+'.patch').read_text()
        try:
            with research_environment(audit_modules=['rich','pygments'],task_wheels=data/'wheels'):
                result=await verify_task(manager,cfg,task,snapshot,base_snapshot_path=base,patch_path=overlay,agent_patch=repair,start_time=time.perf_counter())
            atomic_json(dest/'official_result.json',result.model_dump(mode='json',exclude={'trace'}))
        finally:manager.cleanup_all()
        atomic_json(dest/'structured_verifier.json',audit_verifier(dest))
        atomic_json(dest/'cleanup.json',dict(complete=not manager.sandboxes and not list((dest/'sandbox_tmp').glob('swegemma_sandbox_*'))))
        for label,_ in variants:assert (dest/('diagnostic-'+label+'.json')).exists(),label


if __name__=='__main__':
    import sys
    asyncio.run(run(sys.argv[1]))
