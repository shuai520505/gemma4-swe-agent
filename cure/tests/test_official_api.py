"""Real ADK/compiler/LiteLLM -> mocked HTTP wire. No network/model generation."""
import json
import hashlib
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from cure import MODEL
from cure.runtime_config import ResearchConfig, validate_compiled

ROOT = Path(__file__).resolve().parents[2]


class CureOfficialTests(unittest.IsolatedAsyncioTestCase):
    async def test_research_worker_honors_registered_time_tools_and_early_patch(self):
        import yaml
        from cure.worker import evaluate
        from harness_v2.official import DurableEvaluator
        from swegemma.models import TaskResult
        from harness_v2.outcomes import normalize
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); candidate = root / 'candidate'
            shutil.copytree(ROOT / 'cure/candidates/checklist', candidate)
            config = ResearchConfig(agent_seconds=47, tool_budget=7, output_tokens=2048, thinking_budget=0)
            sampling = yaml.safe_load((candidate / 'sampling.yaml').read_text())
            sampling.update(max_output_tokens=2048); sampling['thinking_config']['thinking_budget'] = 0
            (candidate / 'sampling.yaml').write_text(yaml.safe_dump(sampling))
            task = dict(instance_id='cpu-task', repo='fixture/project', base_commit='base', problem_statement='original CPU issue')
            tasks = root / 'tasks.jsonl'; tasks.write_text(json.dumps(task) + '\n')
            hashes = {n: hashlib.sha256((candidate / n).read_bytes()).hexdigest() for n in ('agent.yaml', 'sampling.yaml', 'prompts/system.md', 'eval_config.yaml')}
            spec = dict(research_config=config.snapshot(), agent_dir=str(candidate), candidate_hashes=hashes,
                tasks_path=str(tasks), snapshots_dir=str(root), wheels_dir=str(root), graph_dir=str(root / 'graphs'), embeddings_dir=str(root / 'embeddings'),
                model_alias=MODEL, model_path=MODEL, base_url='http://127.0.0.1:8000/v1', instance_id='cpu-task', base_commit='base',
                problem_sha256=hashlib.sha256(task['problem_statement'].encode()).hexdigest())
            observed = []
            async def native(_self, *, task, context):
                observed.append((_self.config.budget.time_minutes, _self.config.budget.tool_calls))
                context.submitted_patch = 'cpu partial patch'
                raise TimeoutError('CPU verifier timeout injection')
            out = root / 'run'; out.mkdir()
            with patch.object(DurableEvaluator, 'evaluate_task', native):
                with self.assertRaises(TimeoutError): await evaluate(spec, out)
            self.assertEqual(observed, [(47 / 60, 7)])
            runtime = json.loads((out / 'runtime_config.json').read_text())
            self.assertEqual(runtime['output_reserved'], 2048)
            self.assertEqual((out / 'latest.patch').read_text(), 'cpu partial patch')
            self.assertTrue(json.loads((out / 'worker_done.json').read_text())['cleanup_complete'])
            self.assertFalse((out / 'official_result.json').exists())
            self.assertEqual(normalize(None, started=True)['status'], 'unknown')

    async def test_official_compiler_and_http_request_semantics(self):
        import httpx
        import yaml
        from adk_submission import ModelRegistry, compile_submission
        from google.adk.models.lite_llm import LiteLlm
        from google.adk.models.llm_request import LlmRequest
        from google.genai import types
        from swegemma.context import SwegemmaContext
        from swegemma.config import build_submission_limits
        seen = []; cases = []
        async def send(_client, request, **kwargs):
            self.assertEqual(request.url.host, '127.0.0.1')
            body = json.loads(request.content); seen.append(body)
            return httpx.Response(200, request=request, json=dict(id='cpu-mock', object='chat.completion',
                created=1, model=MODEL, choices=[dict(index=0, finish_reason='stop', message=dict(role='assistant', content='mock response'))],
                usage=dict(prompt_tokens=1, completion_tokens=1, total_tokens=2)))
        with tempfile.TemporaryDirectory() as temp, patch('httpx.AsyncClient.send', send):
            root = Path(temp)
            for thinking in (0, 512, 4096):
                for include in (None, True, False):
                    for seed in (None, 17):
                        with self.subTest(thinking=thinking, include=include, seed=seed):
                            dest = root / f'{thinking}-{include}-{seed}'
                            shutil.copytree(ROOT / 'cure/candidates/checklist', dest)
                            sampling = yaml.safe_load((dest / 'sampling.yaml').read_text())
                            sampling['thinking_config'] = dict(thinking_budget=thinking)
                            if include is not None: sampling['thinking_config']['include_thoughts'] = include
                            if seed is None: sampling.pop('seed')
                            else: sampling['seed'] = seed
                            (dest / 'sampling.yaml').write_text(yaml.safe_dump(sampling))
                            models = ModelRegistry()
                            models.register(MODEL, LiteLlm(model='openai/' + MODEL, api_base='http://127.0.0.1:8000/v1', api_key='EMPTY'))
                            limits, constraints = build_submission_limits()
                            agent = compile_submission(dest, SwegemmaContext().create_tools(), models, limits=limits, generation_constraints=constraints)
                            # Actual ADK tool-turn serialization, not handcrafted OpenAI messages.
                            req = LlmRequest(model=agent.model.model, config=agent.generate_content_config,
                                contents=[types.Content(role='user', parts=[types.Part(text='original issue')]),
                                    types.Content(role='model', parts=[types.Part(text='retained-thought-sentinel', thought=True),
                                        types.Part(function_call=types.FunctionCall(name='read_file', args={'filepath': 'x.py'}))]),
                                    types.Content(role='user', parts=[types.Part(function_response=types.FunctionResponse(name='read_file',
                                        response={'status': 'ok', 'stdout': 'say "hi"'}))])])
                            before = len(seen)
                            async for _ in agent.model.generate_content_async(req): pass
                            self.assertEqual(len(seen), before + 1)
                            body = seen[-1]
                            self.assertEqual(body.get('max_completion_tokens', body.get('max_tokens')), 8192)
                            self.assertEqual(body['chat_template_kwargs']['enable_thinking'], thinking > 0)
                            if thinking: self.assertEqual(body['thinking_token_budget'], thinking)
                            else: self.assertNotIn('thinking_token_budget', body)
                            if seed is not None: self.assertEqual(body['seed'], seed)
                            else: self.assertIsNone(body.get('seed'))
                            history = body['messages']
                            assistant = next(m for m in history if m['role'] == 'assistant')
                            if include is False:
                                self.assertNotIn('retained-thought-sentinel', str(assistant))
                            else: self.assertIn('retained-thought-sentinel', str(assistant))
                            tool = next(m for m in history if m['role'] == 'tool')
                            parsed = json.loads(tool['content'])
                            self.assertIsInstance(parsed, dict)
                            self.assertEqual(parsed['stdout'], 'say "hi"')
                            cases.append(dict(thinking=thinking, include=include, seed=seed, wire=body))
            for arm in ('checklist', 'cure_v01'):
                models = ModelRegistry(); models.register(MODEL, LiteLlm(model='openai/' + MODEL))
                limits, constraints = build_submission_limits()
                agent = compile_submission(ROOT / 'cure/candidates' / arm, SwegemmaContext().create_tools(), models, limits=limits, generation_constraints=constraints)
                validate_compiled(agent, ResearchConfig())
        out = os.environ.get('CURE_CPU_EVIDENCE_DIR')
        if out:
            Path(out).mkdir(parents=True, exist_ok=True)
            (Path(out) / 'http-request-cases.json').write_text(json.dumps(cases, indent=2))

    async def test_observed_context_saves_live_events_without_new_tools(self):
        from google.adk.events import Event
        from google.genai import types
        from cure.observer import ContractObserver
        from harness_v2.evidence import Journal, read_events
        with tempfile.TemporaryDirectory() as temp:
            j = Journal(temp); observer = ContractObserver(j)
            event = Event(author='cure_v01_c', content=types.Content(role='user', parts=[
                types.Part(function_response=types.FunctionResponse(name='run_command', response={'stdout': 'failed'}))]))
            observer.observe(event)
            rows = read_events(Path(temp) / 'contract_observations.jsonl')
            self.assertEqual(rows[0]['tool'], 'run_command')

    async def test_real_subprocess_manager_preserves_patch_checkpoint(self):
        from swegemma.context import SwegemmaContext
        from harness_v2.official import DurableManager
        from harness_v2.evidence import Journal
        with tempfile.TemporaryDirectory() as temp:
            j = Journal(temp); manager = DurableManager(journal=j, base_dir=Path(temp) / 'sandboxes')
            sid = manager.start()
            try:
                ctx = SwegemmaContext(docker_manager=manager, container_id=sid, max_tool_calls=10)
                tools = ctx.create_tools()
                cmd = tools['run_command']
                self.assertEqual(cmd(command="git init -q && git config user.name Test && git config user.email t@example.invalid && printf 'x = 1\\n' > app.py && git add . && git commit -qm base")['status'], 'ok')
                tools['edit_file'](filepath='app.py', old_string='x = 1', new_string='x = 2')
                manager.exec(sid, 'git diff --binary _swegemma_baseline')
                # Native baseline tag is normally created by Evaluator. Explicit submit remains available here.
                result = tools['submit_patch']()
                self.assertEqual(result['status'], 'ok')
                j.patch(ctx.submitted_patch, source='official_six_tool_submit')
                self.assertIn('x = 2', (Path(temp) / 'latest.patch').read_text())
            finally: manager.stop(sid)
