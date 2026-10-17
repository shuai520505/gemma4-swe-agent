import asyncio
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from cure.runtime_config import ResearchConfig
from cure.request_guard import ConfiguredGuard
from cure.observer import ContractObserver
from harness_v2.evidence import Journal, read_events
from harness_v2.context_budget import ContextBudgetExceeded


class RuntimeTests(unittest.IsolatedAsyncioTestCase):
    async def test_output_boundaries_are_checked_before_generation(self):
        cfg = ResearchConfig(); sent = []
        async def generate(**kwargs): sent.append(kwargs); return kwargs
        for excess in (0, 1):
            async def counter(body): return dict(count=32768 - 1024 - cfg.output_tokens + excess, max_model_len=32768)
            guard = ConfiguredGuard(counter, generate, core_issue='complete issue', config=cfg)
            if excess:
                with self.assertRaises(ContextBudgetExceeded): await guard.acompletion(model='openai/m', messages=[])
            else: await guard.acompletion(model='openai/m', messages=[])
        self.assertEqual(len(sent), 1)
        self.assertIn('complete issue', str(sent[0]['messages']))
        self.assertEqual(sent[0]['max_completion_tokens'], cfg.output_tokens)

    async def test_wire_configuration_drift_fails_closed(self):
        async def no_call(**kwargs): self.fail('generation must not occur')
        async def counter(body): self.fail('drift must fail before counting')
        guard = ConfiguredGuard(counter, no_call, core_issue='issue', config=ResearchConfig())
        for extra in ({'max_tokens': 16384}, {'seed': 99}, {'extra_body': {'chat_template_kwargs': {'enable_thinking': False}}}):
            with self.assertRaises(ValueError): await guard.acompletion(model='openai/m', messages=[], **extra)

    async def test_thinking_off_and_parameters(self):
        async def counter(body): return dict(count=20, max_model_len=32768)
        async def generate(**kwargs): return kwargs
        args = await ConfiguredGuard(counter, generate, core_issue='issue', config=ResearchConfig(thinking_budget=0)).acompletion(model='openai/m', messages=[])
        self.assertFalse(args['extra_body']['chat_template_kwargs']['enable_thinking'])
        self.assertNotIn('thinking_token_budget', args['extra_body'])
        self.assertEqual(args['seed'], 17)

    def test_invalid_registered_limits(self):
        for kw in ({'output_tokens': True}, {'thinking_budget': 8192}, {'agent_seconds': 0}, {'tool_budget': -1}, {'seed': None}):
            with self.assertRaises(ValueError): ResearchConfig(**kw)
        cfg = ResearchConfig(agent_seconds=47, tool_budget=7, output_tokens=2048, thinking_budget=0)
        self.assertEqual(cfg.stage_caps['agent'], 77)
        self.assertGreater(cfg.outer_seconds, cfg.agent_seconds + 300)

    def test_passive_observer_labels_claims_and_deduplicates(self):
        with tempfile.TemporaryDirectory() as temp:
            j = Journal(temp); obs = ContractObserver(j)
            response = SimpleNamespace(name='run_command', response={'stdout': 'failed'})
            event = SimpleNamespace(id='1', partial=False, content=SimpleNamespace(parts=[
                SimpleNamespace(function_response=response, text='', thought=False),
                SimpleNamespace(function_response=None, text='<cure>{"action":"edit","evidence":"passed"}</cure>', thought=False)]))
            obs.observe(event); obs.observe(event)
            rows = read_events(Path(temp) / 'contract_observations.jsonl')
            self.assertEqual(len(rows), 2)
            self.assertFalse(rows[1]['affects_controller_decisions'])
            self.assertEqual(rows[1]['provenance'], 'model_report_only_unverified')
