import asyncio
import dataclasses
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from s1.config import Config
from s1.guard import Guard
from harness_v2.context_budget import ContextBudgetExceeded, ContextCountingError

ROOT=Path(__file__).resolve().parents[1]


class CoreTests(unittest.IsolatedAsyncioTestCase):
    async def test_both_context_boundaries(self):
        for cap in (8192,16384):
            for delta in (0,1):
                sent=[]
                async def count(body): return dict(count=32768-1024-cap+delta,max_model_len=32768)
                async def generate(**args): sent.append(args); return args
                guard=Guard(count,generate,config=Config(output_tokens=cap),core_issue='CORE')
                if delta:
                    with self.assertRaises(ContextBudgetExceeded):
                        await guard.acompletion(model='openai/test',messages=[])
                    self.assertFalse(sent)
                else:
                    args=await guard.acompletion(model='openai/test',messages=[])
                    self.assertEqual(args['max_completion_tokens'],cap)
                    self.assertIn('CORE',[m['content'] for m in args['messages']])

    async def test_counter_failure_closed(self):
        async def count(body): raise OSError('unavailable')
        async def generate(**args): self.fail('Sent uncounted request')
        with self.assertRaises(ContextCountingError):
            await Guard(count,generate,config=Config(),core_issue='x').acompletion(model='openai/test')

    async def test_registered_settings_drift_rejected(self):
        async def count(body): return dict(count=1,max_model_len=32768)
        async def gen(**args): self.fail('Drifting request sent')
        for kwargs in (dict(max_completion_tokens=8192),dict(seed=18),
                dict(extra_body={'chat_template_kwargs':{'enable_thinking':False}}),
                dict(extra_body={'thinking_token_budget':512})):
            with self.assertRaises(ValueError):
                await Guard(count,gen,config=Config(),core_issue='x').acompletion(model='openai/test',**kwargs)

    async def test_summary_uses_registered_thinking_off(self):
        async def count(body): return dict(count=1,max_model_len=32768)
        async def gen(**args): return args
        c=Config(output_tokens=8192,thinking_budget=0)
        out=await Guard(count,gen,config=c,core_issue='x').acompletion(model='openai/test')
        self.assertFalse(out['extra_body']['chat_template_kwargs']['enable_thinking'])
        self.assertNotIn('thinking_token_budget',out['extra_body'])
        self.assertEqual(out['seed'],17)

    async def test_invalid_configs(self):
        for k,v in [('agent_seconds',0),('tool_budget',False),('output_tokens',32769),
                ('thinking_budget',-1),('include_thoughts','false'),('seed',True)]:
            with self.assertRaises(ValueError): Config(**{k:v})
        with self.assertRaises(ValueError): Config(output_tokens=4096)

    async def test_stage_and_outer_budget_mapping(self):
        c=Config()
        self.assertEqual(c.outer_seconds,1350)
        self.assertEqual(c.stage_caps['agent'],330)
        self.assertEqual(c.stage_caps['verification'],300)
        self.assertEqual(Config(agent_seconds=120).outer_seconds,1170)

    async def test_single_factor_and_packages(self):
        manifest=json.loads((ROOT/'candidates.json').read_text())
        a=manifest['control']
        for arm,key in [('e1_output8192','output_tokens'),('e2_thinking0','thinking_budget')]:
            changes=[k for k in a['config'] if a['config'][k]!=manifest[arm]['config'][k]]
            self.assertEqual(changes,[key])
            self.assertEqual(a['members']['prompts/system.md'],manifest[arm]['members']['prompts/system.md'])
        for arm in ('e3_locate','e4_verify'):
            self.assertEqual(a['config'],manifest[arm]['config'])
            self.assertEqual(a['members']['agent.yaml'],manifest[arm]['members']['agent.yaml'])
        for arm,info in manifest.items():
            package=ROOT/'packages'/arm/'submission.zip'
            self.assertEqual(hashlib.sha256(package.read_bytes()).hexdigest(),info['zip_sha256'])
            with zipfile.ZipFile(package) as z:
                self.assertIsNone(z.testzip())
                self.assertEqual(set(z.namelist()),{'agent.yaml','eval_config.yaml','prompts/system.md'})
                for n,digest in info['members'].items():
                    self.assertEqual(hashlib.sha256(z.read(n)).hexdigest(),digest)
                self.assertNotIn('cure',z.read('prompts/system.md').decode().lower())

    async def test_collector_unknown_is_not_failed(self):
        from harness_v2.outcomes import normalize,summarize
        raw=dict(resolved=False,test_exit_code=-1,error_message='Agent timed out')
        self.assertEqual(normalize(raw,started=True)['status'],'unknown')
        result=summarize([dict(arm='A',status='resolved'),dict(arm='B',status='unknown')],planned_per_arm={'A':1,'B':1})
        self.assertIsNone(result['A']['resolution_rate'])


if __name__=='__main__': unittest.main()
