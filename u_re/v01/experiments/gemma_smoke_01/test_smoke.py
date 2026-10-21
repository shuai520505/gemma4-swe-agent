"""Own synthetic tests only: no FastAPI test, official Runner, model or Kaggle call."""
import asyncio
from datetime import datetime,timezone,timedelta
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('smoke',HERE/'SMOKE_RUNNER.py')
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
from u_re.v01.experiments.gemma_smoke_01 import inputs as b

class Toy:
    def __init__(self):self.tools=[];self.text='def ok(n): return n > 0';self.cleaned=False
    def tool(self,name,**kw):
        self.tools.append(name)
        if name=='get_status':return {'remaining_seconds':280,'remaining_tool_calls':59}
        if name=='read_file':return self.text
        if name=='write_file':return {'diagnostic_created':True}
        if name=='edit_file':self.text='def ok(n): return n >= 0';return {'edited':True}
        if name=='run_command':
            scope={};exec(self.text,scope)
            return {'exit_code':0 if scope['ok'](0) and scope['ok'](1) and not scope['ok'](-1) else 1}
        if name=='submit_patch':return {'success':True,'patch':'synthetic toy diff'}
        raise ValueError(name)
    def __call__(self,stage,**kw):
        assert kw['tools']==b.TOOLS
        if stage=='LOAD_MODEL':return {'usage':None,'model_transport':'mock'}
        if stage=='INIT_AGENT':self.tool('get_status')
        if stage=='LOAD_TASK':self.tool('read_file')
        if stage=='RUN_AGENT':self.tool('write_file')
        if stage=='RUN_AGENT':
            assert self.tool('run_command')['exit_code']==1
        if stage=='COLLECT_PATCH':self.tool('edit_file');return {'patch':'synthetic toy diff'}
        if stage=='NATIVE_VERIFY':
            assert self.tool('run_command')['exit_code']==0
        if stage=='NATIVE_VERIFY':
            self.tool('submit_patch');return {'TaskResult':{'resolved':True,'test_exit_code':0},'usage':None}
        if stage=='CLEANUP':self.cleaned=True
        return {}

class SmokeTests(unittest.TestCase):
    def grant(self,p):
        return dict(experiment_id=s.EXPERIMENT,task='fastapi_14492',candidate='noegv',agent_runs=1,
            agent_seconds=300,tool_budget=60,gpu_count=4,gpu_type='NVIDIA L4',formal_submission=False,
            gpu_authorized=True,protocol_sha256=s.digest(p),human_authorization_reference='synthetic-test-only',
            isolation_review_reference='synthetic-test-only',expires_utc=(datetime.now(timezone.utc)+timedelta(minutes=1)).isoformat())
    def test_end_to_end_mock_six_tool_contract(self):
        with tempfile.TemporaryDirectory() as d:
            toy=Toy();result=s.mock_run(d,toy)
            self.assertTrue(result['resolved']);self.assertTrue(toy.cleaned)
            self.assertEqual(set(toy.tools),set(b.TOOLS));self.assertEqual(toy.tools.count('submit_patch'),1)
            events=json.loads((Path(d)/'STAGES.json').read_text(encoding='utf-8'))
            self.assertEqual([x['stage'] for x in events['stages']],s.STAGES)
            self.assertTrue(all(x['status']=='PASS' and x['mock'] for x in events['stages']))
            self.assertIsNone(events['stages'][0]['token_usage'])
    def test_cleanup_after_transport_error(self):
        with tempfile.TemporaryDirectory() as d:
            toy=Toy()
            def broken(stage,**kw):
                if stage=='LOAD_MODEL':raise ConnectionError('synthetic')
                return toy(stage,**kw)
            with self.assertRaises(ConnectionError):s.mock_run(d,broken)
            self.assertTrue(toy.cleaned)
            self.assertEqual(json.loads((Path(d)/'STAGES.json').read_text(encoding='utf-8'))['stages'][1]['error_class'],'ConnectionError')
    def test_missing_authorization_before_runtime(self):
        with tempfile.TemporaryDirectory() as d,patch.object(s,'runtime_files') as runtime:
            with self.assertRaises(PermissionError):asyncio.run(s.run_authorized({}, {},d))
            runtime.assert_not_called()
    def test_grant_pin_scope_expiry_and_isolation(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'plan';p.write_text('test')
            good=self.grant(p);s.authorize(good,p)
            for k,v in [('agent_runs',2),('candidate','full'),('gpu_count',1),('formal_submission',True),
                        ('protocol_sha256','wrong'),('human_authorization_reference',''),('isolation_review_reference',''),
                        ('expires_utc','2000-01-01T00:00:00+00:00')]:
                with self.subTest(k=k),self.assertRaises(PermissionError):s.authorize(dict(good,**{k:v}),p)
    def test_no_reentry(self):
        with tempfile.TemporaryDirectory() as d:
            s.claim_once(d)
            with self.assertRaises(FileExistsError):s.claim_once(d)
    def test_frozen_candidates_crc_members(self):
        pins={arm:b.candidate(s.ROOT/f'u_re/v01/submission_{arm}.zip',h) for arm,h in b.ZIPS.items()}
        self.assertEqual([n for n in b.MEMBERS if pins['noegv']['members'][n]!=pins['full']['members'][n]],['prompts/system.md'])
    def test_candidate_tamper(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'zip';p.write_bytes(b'bad')
            with self.assertRaises(AssertionError):b.candidate(p,b.ZIPS['noegv'])
    def test_agent_projection_rejects_all_evaluator_fields(self):
        clean=dict(instance_id='toy',repo='local/toy',base_commit='x',problem_statement='Synthetic')
        self.assertEqual(b.agent_input(clean),clean)
        for k in ('test_patch','patch','gold_patch','reference_patch','TaskResult','trace','junit','other_arm'):
            with self.subTest(k=k),self.assertRaises(ValueError):b.agent_input(dict(clean,**{k:'not allowed'}))
    def test_no_distribution_fetch_or_dispatch_in_runner(self):
        import ast
        tree=ast.parse((HERE/'SMOKE_RUNNER.py').read_text(encoding='utf-8'))
        attrs=[n.attr for n in ast.walk(tree) if isinstance(n,ast.Attribute)]
        self.assertFalse(set(attrs)&{'kernels_push','save_kernel','SaveKernel','submit','install'})
        draft=json.loads((HERE/'GPU_PREFLIGHT.json').read_text(encoding='utf-8'))
        self.assertFalse(draft['gpu_authorized']);self.assertFalse(draft['execute'])

if __name__=='__main__':unittest.main(verbosity=2)
