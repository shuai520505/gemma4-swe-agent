"""Real Linux organizer Runner/tools/Verifier; synthetic toy, scripted HTTP only."""
import asyncio
import importlib.metadata
import json
from pathlib import Path
import sys
import time

async def run(output):
    import torch
    assert sys.platform=='linux' and torch.cuda.device_count()==0
    from harness_v2.evidence import atomic_json,Journal
    from u_re.v01.runner_cases import exercise
    from swegemma.harness.verification import verify_task
    from swegemma.models import Task
    from swegemma.config import EvalConfig
    from adk_submission import ModelRegistry
    from s1.verifier_v3.environment import SubprocessManager,research_environment
    from s1.verifier_v3.audit import audit_verifier
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    atomic_json(output/'versions.json',{p:importlib.metadata.version(p) for p in
        ('swegemma','adk-submission','google-adk','google-genai','litellm','pytest')})
    from adk_submission import compile_submission
    from swegemma.context import SwegemmaContext
    from google.adk.models.lite_llm import LiteLlm
    from s1.config import Config,validate_compiled
    from .inputs import candidate,ZIPS
    here=Path(__file__).resolve().parents[2]
    candidate(here/'submission_noegv.zip',ZIPS['noegv'])
    models=ModelRegistry();models.register('gemma-4-31b-it-qat-w4a16-ct',LiteLlm(
        model='openai/gemma-4-31b-it-qat-w4a16-ct',api_base='http://127.0.0.1:8000/v1',api_key='EMPTY'))
    agent=compile_submission(here/'candidate_noegv',SwegemmaContext().create_tools(),models)
    validate_compiled(agent,Config())
    compiled=dict(single_LlmAgent=not agent.sub_agents,tools=6,NoEGV=True)
    results=[]
    for case in ('basic','closed_loop','wrong_test','exact_tools','external_cancel','post_submit_negative'):
        directory=output/'cases'/case
        r=await exercise('noegv',case,directory)
        assert json.loads((directory/'cleanup.json').read_text(encoding='utf-8'))['complete']
        if case=='external_cancel':
            # Production audit correctly refuses unproven server-side reclamation.
            # This fixture deliberately cancels the mocked transport externally,
            # so retain audit=false and independently check the fixture's evidence.
            assert r['external_cancellation_propagated'] and r['HTTP_cancelled']
            assert r['HTTP_audit']['reasons']==['unexplained_cancellation']
            cancelled=[row for row in r['HTTP_audit']['rows'] if row['terminal_status']=='cancelled']
            assert len(cancelled)==1 and cancelled[0]['usage'] is None
        else:assert r['HTTP_audit']['passed'],case
        boundary=json.loads((directory/'boundary.json').read_text(encoding='utf-8'))
        assert boundary['budget_seconds']==300 and boundary['tools_limit']==60 and boundary['command_seconds']==120
        for w in r['wire_configuration']:
            assert set(w['tool_names'])=={'get_status','run_command','read_file','edit_file','write_file','submit_patch'}
            assert (w['output'],w['thinking'],w['seed'],w['sampling'])==(16384,4096,17,{})
        if case=='exact_tools':assert r['counted_tools']==60
        if case=='external_cancel':assert r['external_cancellation_propagated']
        if case=='post_submit_negative':assert len(r['tools_after_first_successful_submit'])>0 and r['successful_submits']==2
        if case=='closed_loop':assert r['counterexample_revision_retest']
        results.append(dict(case=case,passed=True,counted_tools=r['counted_tools'],successful_submits=r['successful_submits']))
    # A new, owned synthetic overlay tests the genuine native Phase2/JUnit/TaskResult path.
    # It contains no competition test, task, reference repair or historical result.
    directory=output/'native_toy_verifier';directory.mkdir()
    test_patch='''diff --git a/test_synthetic.py b/test_synthetic.py
new file mode 100644
--- /dev/null
+++ b/test_synthetic.py
@@ -0,0 +1,4 @@
+import app
+def test_boundary():
+    assert app.accepts(0)
+    assert app.accepts(1) and not app.accepts(-1)
'''
    task=Task(instance_id='ure_smoke_owned_toy',repo='test/ure_toy',base_commit='synthetic',
        problem_statement='Owned synthetic inclusive boundary.',test_patch=test_patch)
    manager=SubprocessManager(journal=Journal(directory),base_dir=directory/'sandbox_tmp',audit_modules=['app'],timeout_seconds=120)
    manager.agent_id='evaluator_only'
    cfg=EvalConfig(tasks_path=directory/'unused.jsonl',snapshots_dir=directory,results_dir=directory/'native',
        submission_dir=Path(__file__).resolve().parents[2]/'candidate_noegv',models=ModelRegistry(),
        sandbox='subprocess',verification_timeout_seconds=300,enable_sandbox_testing=True,display_mode='quiet')
    try:
        with research_environment(audit_modules=['app']):
            result=await verify_task(manager,cfg,task,output/'cases/basic/baseline.tgz',
                agent_patch=(output/'cases/basic/returned.patch').read_text(encoding='utf-8'),start_time=time.perf_counter())
        atomic_json(directory/'official_result.json',result.model_dump(mode='json',exclude={'trace'}))
    finally:manager.cleanup_all()
    audit=audit_verifier(directory)
    atomic_json(directory/'native_audit.json',audit)
    assert result.resolved and result.test_exit_code==0
    assert (directory/'phase2.junit.xml').is_file() and not audit['infrastructure_stop']
    atomic_json(directory/'cleanup.json',dict(complete=not manager.sandboxes))
    atomic_json(output/'CPU_INTERFACE_GATE.json',dict(passed=True,compiled=compiled,cases=results,
        native_TaskResult=True,native_JUnit=True,official_Runner=True,official_tools=True,
        synthetic_only=True,GPU=False,Gemma_inference=False,competition_task_executed=False))
    print('U_RE_SMOKE_CPU_INTERFACES_PASS',flush=True)

if __name__=='__main__':asyncio.run(run(sys.argv[1]))
