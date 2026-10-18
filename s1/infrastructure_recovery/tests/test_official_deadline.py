"""Actual official Agent Harness -> Compiler -> ADK -> real stalled TCP request."""
import asyncio
import json
import os
from pathlib import Path
import subprocess
import tarfile
import unittest

from harness_v2.evidence import Journal,atomic_json
from s1 import MODEL
from s1.infrastructure_recovery.wire import observe_http,audit_requests
from . import test_wire


class OfficialDeadlineTests(unittest.IsolatedAsyncioTestCase):
    asyncSetUp=test_wire.WireTests.asyncSetUp
    asyncTearDown=test_wire.WireTests.asyncTearDown

    async def test_native_Agent_deadline_reaches_observer_and_preserves_patch_trace(self):
        from swegemma.harness.agent_runner import run_agent_sandbox
        from swegemma.config import EvalConfig
        from swegemma.models import Task
        from adk_submission import ModelRegistry
        from google.adk.models.lite_llm import LiteLlm,LiteLLMClient
        from harness_v2.official import DurableManager,DurableContext,GuardedClient
        from s1.guard import Guard
        from s1.config import Config
        root=self.directory;source=root/'base';source.mkdir()
        (source/'calc.py').write_text('VALUE=1\n')
        subprocess.run(['git','init','-q',str(source)],check=True)
        snapshot=root/'base.tgz'
        with tarfile.open(snapshot,'w:gz') as tar:tar.add(source,arcname='.')
        task=Task(instance_id='native_cancel_cpu',repo='test/mock_repo',base_commit='123456',problem_statement='CPU cancellation fixture only')
        async def counter(body):return dict(count=100,max_model_len=32768)
        model=LiteLlm(model='openai/'+MODEL,api_base=self.url.removesuffix('/chat/completions'),api_key='EMPTY')
        journal=Journal(root/'evidence')
        model.llm_client=GuardedClient(Guard(counter,LiteLLMClient().acompletion,
            config=Config(),core_issue=task.problem_statement,emit=journal.append))
        models=ModelRegistry();models.register(MODEL,model)
        repo=Path(__file__).resolve().parents[3]
        config=EvalConfig(tasks_path=root/'unused.jsonl',snapshots_dir=root,results_dir=root/'native',
            submission_dir=repo/'s1/candidates/control',models=models,sandbox='subprocess',max_time_minutes=.05,
            max_tool_calls=60,timeout_seconds=120,display_mode='quiet',enable_sandbox_testing=True)
        manager=DurableManager(journal=journal,base_dir=root/'sandboxes')
        context=DurableContext(journal=journal,docker_manager=manager,task=task,budget=config.budget,harness=config.harness)
        manager.context=context
        try:
            with observe_http(root/'evidence'):
                patch,error,trace=await run_agent_sandbox(manager,config,task,snapshot,context=context)
            self.assertTrue(self.accepted.is_set(),'Actual model HTTP never reached the TCP server')
            self.assertIn('Agent exceeded session timeout',error)
            self.assertLess(context.agent_elapsed_seconds,6)
            self.assertGreaterEqual(context.agent_elapsed_seconds,2.5)
            manager.cleanup_all()
            result=audit_requests(root/'evidence',deadline_evidence=dict(official_agent_deadline=True,cleanup_verified=not manager.sandboxes))
            self.assertTrue(result['passed'],result)
            self.assertEqual(result['rows'][0]['terminal_status'],'cancelled')
            self.assertTrue(result['partial_token_usage'])
            out=os.environ.get('S1_RECOVERY_EVIDENCE')
            if out:
                dest=Path(out)/'native_deadline';dest.mkdir(parents=True,exist_ok=False)
                atomic_json(dest/'result.json',dict(native_agent_error=error,native_agent_seconds=context.agent_elapsed_seconds,
                    patch=patch,wire=result,real_official_Harness=True,real_ADK_Runner=True,
                    real_HTTP_socket=True,Gemma_inference=False))
                atomic_json(dest/'native_trace.json',trace.to_dict())
                for name in ('http_wire.jsonl','http_lifecycle.jsonl','events.jsonl'):
                    (dest/name).write_bytes((root/'evidence'/name).read_bytes())
        finally:manager.cleanup_all()
