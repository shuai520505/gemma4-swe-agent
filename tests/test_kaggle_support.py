"""Offline diagnostics/controller tests; these do not run Gemma or Kaggle tasks."""
import asyncio
import hashlib
import json
from pathlib import Path
import stat
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile

from adk_eval_core.tracing import SessionTrace
from google.adk.events import Event
from google.genai import types
from swegemma.config import EvalConfig, build_submission_limits
from swegemma.context import SwegemmaContext
from swegemma.evaluate import Evaluator
from swegemma.models import TaskResult
from notebooks.kaggle_support import (MODEL_NAME, SUBMISSION_FILES, admission_seconds,
    budget_profile, discover_inputs, evaluate_with_deadline, extract_submission, persist_result)
from scripts.build_kaggle_notebook import ROOT, build


class KagglePreflightTests(unittest.TestCase):
    def inputs(self, root):
        data = root / 'competitions/gemma-4-developer-agent'
        for name in ('snapshots', 'wheels', 'graphs', 'embeddings', 'sample_submission'):
            (data / name).mkdir(parents=True)
        for name in ('tasks.jsonl', 'HARNESS_README.md', 'sample_submission/agent.yaml'):
            (data / name).write_text('fixture')
        wheel = root / 'datasets/metric/gemma-4-developer-agent-wheelhouse'
        wheel.mkdir(parents=True)
        (wheel / 'swegemma-0.2.11-py3-none-any.whl').write_text('fixture')
        model = root / 'models/google/gemma-4/other' / MODEL_NAME / '2'
        model.mkdir(parents=True)
        (model / 'config.json').write_text('{}')
        (model / 'model-00001.safetensors').write_text('fixture')
        archive = root / 'datasets/participant/arbitrary-slug/submission.zip'
        archive.parent.mkdir(parents=True)
        archive.write_bytes((ROOT / 'submission.zip').read_bytes())
        return data, model, archive

    def test_new_layout_and_arbitrary_zip_slug_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            data, model, archive = self.inputs(root)
            paths = discover_inputs(root)
            self.assertEqual(paths['zip'], archive)
            self.assertEqual(paths['data'], data)
            self.assertEqual(paths['model'], model)
            digest = extract_submission(archive, root / 'working/submission')
            self.assertEqual(digest, hashlib.sha256(archive.read_bytes()).hexdigest())
            self.assertEqual({p.relative_to(root / 'working/submission').as_posix()
                              for p in (root / 'working/submission').rglob('*') if p.is_file()}, SUBMISSION_FILES)

    def test_old_layout_and_duplicate_archive(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            data, model, archive = self.inputs(root)
            legacy_data = root / 'gemma-4-developer-agent'
            data.rename(legacy_data)
            self.assertEqual(discover_inputs(root)['data'], legacy_data)
            other = root / 'second/submission.zip'
            other.parent.mkdir()
            other.write_bytes(archive.read_bytes())
            with self.assertRaisesRegex(RuntimeError, 'expected one mounted input'):
                discover_inputs(root)
            self.assertEqual(discover_inputs(root, {'zip': archive})['zip'], archive)

    def test_missing_authorized_input_fails_without_network(self):
        with tempfile.TemporaryDirectory() as temp, patch('urllib.request.urlopen') as network:
            with self.assertRaisesRegex(RuntimeError, '401 means account authorization'):
                discover_inputs(Path(temp))
            network.assert_not_called()

    def test_zip_rejects_unapproved_members_and_symlinks(self):
        for bad_member, symlink in [('.. /agent.yaml', False), ('agent.yaml', True)]:
            with self.subTest(bad_member=bad_member, symlink=symlink), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                archive = root / 'bad.zip'
                with zipfile.ZipFile(archive, 'w') as z:
                    for name in SUBMISSION_FILES:
                        info = zipfile.ZipInfo(bad_member if name == 'agent.yaml' else name)
                        if name == 'agent.yaml' and symlink:
                            info.external_attr = (stat.S_IFLNK | 0o777) << 16
                        z.writestr(info, b'fixture')
                with self.assertRaises(ValueError):
                    extract_submission(archive, root / 'extracted')
                self.assertFalse((root / 'extracted').exists())

    def test_budget_and_actual_eval_config(self):
        batch = budget_profile('batch')
        self.assertLess(batch['max_tasks'] * batch['task_wall_minutes'] + 45 + 15, 720)
        self.assertEqual(budget_profile('single')['max_time_minutes'], 60)
        self.assertEqual(admission_seconds(0, 12, now=700 * 60), 0)
        self.assertEqual(admission_seconds(0, 12, now=690 * 60), 720)
        # Test the actual pinned organizer API; no inference is invoked.
        from adk_submission import ModelRegistry
        limits, constraints = build_submission_limits()
        config = EvalConfig(tasks_path=Path('tasks.jsonl'), snapshots_dir=Path('snapshots'),
            results_dir=Path('results'), submission_dir=ROOT / 'submission', models=ModelRegistry(),
            sandbox='subprocess', max_time_minutes=batch['max_time_minutes'],
            max_tool_calls=batch['max_tool_calls'], timeout_seconds=batch['timeout_seconds'],
            verification_timeout_seconds=batch['verification_timeout_seconds'],
            limits=limits, generation_constraints=constraints, concurrency=1)
        evaluator = Evaluator(config)
        self.assertEqual(evaluator.config.budget.time_minutes, 8)
        self.assertEqual(evaluator.config.harness.verification_timeout_seconds, 300)
        self.assertEqual(evaluator.config.harness.command_timeout_seconds, 120)

    def test_embedded_notebook_is_current_and_executable_syntax(self):
        notebook = build()  # build compiles every cell with top-level-await support.
        self.assertEqual(notebook, json.loads((ROOT / 'notebooks/v0_official.ipynb').read_text()))
        for cell in notebook['cells']:
            if cell['cell_type'] == 'code':
                self.assertIsNone(cell['execution_count'])
                self.assertEqual(cell['outputs'], [])


class EvidenceTests(unittest.TestCase):
    def result(self, with_submit=True, with_tests=True, resolved=False):
        trace = SessionTrace()
        trace.start()
        trace.record_custom('text', content='synthetic model output for diagnostics test', author='fixture')
        if with_submit:
            trace.record_event(Event(author='fixture', invocation_id='fixture',
                content=types.Content(role='model', parts=[types.Part(function_call=
                    types.FunctionCall(name='submit_patch', args={}))])))
            trace.record_event(Event(author='fixture', invocation_id='fixture',
                content=types.Content(role='user', parts=[types.Part(function_response=
                    types.FunctionResponse(name='submit_patch', response={'status': 'ok', 'patch_size': 20}))])))
        return TaskResult(instance_id='fixture-task', repo='test/mock_repo', resolved=resolved,
            agent_patch='synthetic patch', test_output='STDOUT:\n1 failed\nSTDERR:\n' if with_tests else 'patch failed',
            test_exit_code=1, total_llm_calls=1, tool_calls=2, trace=trace,
            error='synthetic test failure')

    def test_failed_verification_preserved_without_inventing_score(self):
        with tempfile.TemporaryDirectory() as temp:
            result = self.result()
            record = persist_result(result, temp)
            self.assertTrue(record['phase2_tests_ran'])
            self.assertTrue(record['first_task_goal_completed'])
            self.assertFalse(record['resolved'])
            self.assertIsNone(record['competition_score'])
            self.assertEqual((Path(temp) / 'agent.patch').read_text(), result.agent_patch)
            self.assertIn('1 failed', (Path(temp) / 'phase2.log').read_text())
            self.assertTrue((Path(temp) / 'model_events.jsonl').stat().st_size)
            self.assertIn('submit_patch', (Path(temp) / 'tool_events.jsonl').read_text())

    def test_missing_submit_or_tests_never_meets_goal(self):
        for submit, tests in [(False, True), (True, False)]:
            with self.subTest(submit=submit, tests=tests), tempfile.TemporaryDirectory() as temp:
                record = persist_result(self.result(submit, tests), temp)
                self.assertFalse(record['first_task_goal_completed'])

    def test_trace_recovery_from_official_artifact(self):
        with tempfile.TemporaryDirectory() as temp:
            result = self.result()
            result.trace.save(Path(temp) / 'native.json')
            result.trace = None
            result.trace_path = str(Path(temp) / 'native.json')
            self.assertTrue(persist_result(result, Path(temp) / 'task')['explicit_submit_patch_success'])


class DeadlineTests(unittest.IsolatedAsyncioTestCase):
    async def test_timeout_preserves_patch_and_exception(self):
        class SlowEvaluator:
            async def evaluate_task(self, **kwargs):
                await asyncio.Event().wait()
        with tempfile.TemporaryDirectory() as temp:
            context = SwegemmaContext()
            context.submitted_patch = 'partial synthetic patch'
            task = SimpleNamespace(instance_id='fixture-timeout')
            with self.assertRaises(TimeoutError):
                await evaluate_with_deadline(SlowEvaluator(), task, context, temp, 0.01)
            self.assertEqual((Path(temp) / 'last_submitted.patch').read_text(), context.submitted_patch)
            self.assertFalse(json.loads((Path(temp) / 'exception.json').read_text())['real_task_completed'])
            self.assertFalse((Path(temp) / 'result.json').exists())

    async def test_controller_saves_actual_return_value(self):
        result = EvidenceTests().result()
        class ReturnedEvaluator:
            async def evaluate_task(self, **kwargs):
                return result
        with tempfile.TemporaryDirectory() as temp:
            record = await evaluate_with_deadline(ReturnedEvaluator(), SimpleNamespace(instance_id='fixture-task'),
                                                  SwegemmaContext(), temp, 2)
            self.assertFalse(record['resolved'])
            self.assertTrue(json.loads((Path(temp) / 'live_status.json').read_text())['completed'])
