"""Deterministic offline tests. No ADK Agent, Notebook or inference is launched."""
import ast
import asyncio
import json
from types import SimpleNamespace
import unittest

from harness_v2.context_budget import ContextPolicy, ContextBudgetExceeded, ContextCountingError, RequestGuard
from .context_audit import HERE, ROOT, ARCHIVE_REL, admission, analyze, prior_context_comparison
from .source_audit import wheel_sources


class GuardBoundary(unittest.TestCase):
    def test_registered_output_cap_and_thinking_are_bound_together(self):
        from s1.guard import Guard
        from s1.config import Config
        generated=[]
        async def count(body):return dict(count=20000,max_model_len=32768)
        async def generate(**kw):generated.append(kw);return kw
        guard=Guard(count,generate,core_issue='OWNED',config=Config(output_tokens=8192))
        result=asyncio.run(guard.acompletion(model='owned',messages=[dict(role='user',content='OWNED')],max_completion_tokens=8192))
        self.assertEqual(result['max_completion_tokens'],8192)
        self.assertEqual(result['extra_body']['thinking_token_budget'],4096)
        self.assertEqual(result['seed'],17)
        with self.assertRaises(ValueError):
            asyncio.run(guard.acompletion(model='owned',messages=[],max_completion_tokens=16384))
        self.assertEqual(len(generated),1)
    def test_all_three_exact_boundaries_match_registered_code(self):
        for output,cap in ((16384,15360),(12288,19456),(8192,23552)):
            self.assertEqual(ContextPolicy().check(cap,output)['decision'],'allow')
            self.assertTrue(admission(cap,output)['admitted'])
            with self.assertRaises(ContextBudgetExceeded):ContextPolicy().check(cap+1,output)
            self.assertFalse(admission(cap+1,output)['admitted'])

    def test_invalid_observations_are_not_silently_counts(self):
        for value in (True,1.5,-1,None):
            with self.assertRaises(ContextCountingError):ContextPolicy().check(value,16384)
            with self.assertRaises(ValueError):admission(value,16384)

    def test_rejected_request_never_reaches_generation(self):
        generated=[];emitted=[]
        async def count(body):return dict(count=15361,max_model_len=32768)
        async def generate(**kw):generated.append(kw)
        guard=RequestGuard(count,generate,core_issue='OWNED_ISSUE',emit=emitted.append)
        with self.assertRaises(ContextBudgetExceeded):
            asyncio.run(guard.acompletion(model='openai/owned',messages=[dict(role='user',content='OWNED_ISSUE')],max_completion_tokens=16384))
        self.assertEqual(generated,[])
        self.assertEqual(emitted[-1]['decision'],'reject')

    def test_exact_Issue_restoration_is_idempotent_on_synthetic_summary(self):
        generated=[];emitted=[]
        async def count(body):return dict(count=100,max_model_len=32768)
        async def generate(**kw):generated.append(kw);return kw
        guard=RequestGuard(count,generate,core_issue='OWNED_ISSUE',emit=emitted.append)
        first=asyncio.run(guard.acompletion(model='owned',messages=[dict(role='user',content='synthetic summary')],max_tokens=16384))
        self.assertTrue(emitted[-1]['core_restored'])
        second=asyncio.run(guard.acompletion(**first))
        self.assertFalse(emitted[-1]['core_restored'])
        self.assertEqual(sum(m['content'].count('OWNED_ISSUE') for m in second['messages']),1)


class ActualArchive(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.data=analyze(ROOT.parent/'private-evidence'/ARCHIVE_REL)

    def test_all40_serving_counts_match_received_prompt_usage(self):
        records=self.data['completed_requests'];self.assertEqual(len(records),40)
        self.assertTrue(all(r['input_tokens']==r['prompt_tokens'] for r in records))
        self.assertEqual(sum(r['total_received_tokens'] for r in records),314334)
        self.assertTrue(all(r['response_status']==200 for r in records))

    def test_no_compaction_restoration_or_duplicate_message_explanation(self):
        for r in self.data['completed_requests']:
            self.assertEqual(r['stable_prefix_messages'],r['previous_message_count'])
            self.assertEqual(r['duplicate_exact_messages_in_request'],0)
            self.assertEqual(r['exact_Issue_occurrences'],1)
            self.assertFalse(r['Issue_restored'])
            self.assertIsNone(r['component_token_counts'])
        self.assertTrue(all(not s['compaction_events'] for s in self.data['sessions']))

    def test_source_deployment_excluded_and_repetition_not_invented(self):
        self.assertEqual(sum(s['observed_production_edits'] for s in self.data['sessions']),0)
        self.assertEqual(sum(s['total_returned_read_lines'] for s in self.data['sessions']),1833)
        self.assertEqual(sum(s['repeated_same_path_lines'] for s in self.data['sessions']),1)

    def test_shadow_opportunity_is_not_a_real_request_or_outcome(self):
        rows=self.data['shadow_admissions']
        self.assertEqual(len(rows),129)
        self.assertEqual(sum(r['actually_sent'] for r in rows),120)
        self.assertEqual(sum(r['admitted'] for r in rows if r['output_reservation']==16384),40)
        self.assertEqual(sum(r['admitted'] for r in rows if r['output_reservation']==8192),43)
        self.assertTrue(all(r['native_resolved'] is None for r in self.data['observed_missing_sessions']))
        self.assertEqual(sorted(r['input_tokens'] for r in self.data['guard_rejections']),[15607,15684,15989])

    def test_replay_serialization_is_deterministic(self):
        again=analyze(ROOT.parent/'private-evidence'/ARCHIVE_REL)
        self.assertEqual(json.dumps(self.data,sort_keys=True),json.dumps(again,sort_keys=True))

    def test_prior_context_gain_did_not_add_native_success(self):
        cases=prior_context_comparison()['cases']
        for cap in (16384,8192):
            selected=[r for r in cases if r['output_reservation']==cap]
            self.assertEqual(sum(r['native_resolved'] for r in selected),1)
        self.assertEqual(sum(r['guard_rejections'] for r in cases if r['output_reservation']==8192),0)
        self.assertTrue(any(not r['usage_complete'] for r in cases))


class PinnedInterface(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.sources,_=wheel_sources()

    def function(self,path,name,namespace):
        tree=ast.parse(self.sources[path]);node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
        exec('from __future__ import annotations\n'+ast.unparse(node),namespace)
        return namespace[name]

    def test_named_callbacks_without_registry_are_not_enforcement(self):
        fn=self.function('adk_submission/resolvers/callbacks.py','resolve_callback_fields',{})
        result=fn(SimpleNamespace(before_model_callbacks=['owned_controller']),SimpleNamespace(callback_registry=None),[])
        self.assertEqual(result,{})

    def test_include_contents_none_keeps_single_task_tool_history(self):
        # Execute the pinned selection function with minimal pure dependencies;
        # this is a window-selection test, not an actual ADK Agent run.
        fn=self.function('google/adk/flows/llm_flows/contents.py','_get_current_turn_contents',dict(
            _should_include_event_in_context=lambda branch,event:True,
            _is_other_agent_reply=lambda name,event:event.author not in ('user',name),
            _get_contents=lambda branch,events,name,**kwargs:events))
        events=[SimpleNamespace(author='user')]+[SimpleNamespace(author='owned_agent') for _ in range(20)]
        self.assertEqual(len(fn(None,events,'owned_agent')),21)
        self.assertEqual(len(fn(None,events+[SimpleNamespace(author='user')],'owned_agent')),1)

    def test_research_compaction_is_not_a_competitor_agent_field(self):
        tree=ast.parse(self.sources['adk_submission/schema.py'])
        cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='SandboxedLlmAgentConfig')
        fields={n.target.id for n in cls.body if isinstance(n,ast.AnnAssign) and isinstance(n.target,ast.Name)}
        self.assertNotIn('events_compaction_config',fields)
        self.assertIn('include_contents',fields)
        self.assertIn('skills',fields)


if __name__=='__main__':unittest.main(verbosity=2)
