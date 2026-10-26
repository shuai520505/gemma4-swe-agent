"""Executable negative interface tests, not a production mechanism spike.

Complete pinned Pydantic schemas/registries run locally. SDK-dependent method
bodies run in isolated namespaces with explicit external test doubles. No
official Runner, Google module, historical candidate or evaluator is patched.
"""
import ast
import asyncio
from contextlib import aclosing
import copy
from types import SimpleNamespace as NS
import unittest

from pydantic import ValidationError

from .interface_sources import fragment, historical_bypass, node_at, pinned_sources, schema_modules

SCHEMA = 'adk_submission/schema.py'
CALLBACKS = 'adk_submission/resolvers/callbacks.py'
SEQUENTIAL = 'google/adk/agents/sequential_agent.py'
LOOP = 'google/adk/agents/loop_agent.py'
SKILL = 'google/adk/tools/skill_toolset.py'


class RestrictedSchema(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.modules = schema_modules()
        cls.schema = cls.modules['schema']

    def validate(self, **fields):
        return self.schema.SandboxedAgentConfig.model_validate(dict(
            name='owned_interface_fixture', instruction='Public synthetic Issue.', **fields)).root

    def test_only_four_agent_classes_are_accepted(self):
        self.assertEqual(self.validate().agent_class, 'LlmAgent')
        for kind in ('SequentialAgent', 'LoopAgent', 'ParallelAgent'):
            item = self.schema.SandboxedAgentConfig.model_validate(dict(
                name='owned', agent_class=kind, sub_agents=[])).root
            self.assertEqual(item.agent_class, kind)
        for kind in ('ScriptAgent', 'CustomAgent', 'BaseAgent'):
            with self.assertRaises(ValidationError):
                self.validate(agent_class=kind)

    def test_global_projection_and_factory_fields_are_rejected(self):
        for key in ('events_compaction_config', 'history_processor', 'before_inference',
                    'code_executor', 'agent_factory', 'callback_registry', 'state'):
            with self.subTest(key=key), self.assertRaises(ValidationError):
                self.validate(**{key: {}})

    def test_workflow_has_no_script_or_tool_operation_field(self):
        for key in ('script', 'tools', 'skills', 'command', 'operation'):
            with self.subTest(key=key), self.assertRaises(ValidationError):
                self.schema.SandboxedAgentConfig.model_validate(dict(
                    agent_class='SequentialAgent', name='owned', sub_agents=[], **{key: []}))

    def test_subagent_refs_do_not_accept_code_or_path_escape(self):
        for ref in ({'code': 'owned.module:preflight'}, {'config_path': '../outside.yaml'},
                    {'config_path': 'owned.yaml', 'code': 'owned.module:preflight'}):
            with self.subTest(ref=ref), self.assertRaises(Exception):
                self.schema.SubAgentRef.model_validate(ref)

    def test_generation_has_no_force_skill_or_model_callback_code(self):
        for key in ('tool_choice', 'tools', 'system_instruction', 'before_model_callback'):
            with self.subTest(key=key), self.assertRaises(ValidationError):
                self.validate(generate_content_config={key: 'run_skill_script'})
        with self.assertRaises(ValidationError):
            self.validate(before_model_callbacks=[{'code': 'owned.py:project'}])

    def test_callback_names_without_organizer_registry_are_inert(self):
        config = self.validate(before_model_callbacks=['owned_preflight'],
                               before_agent_callbacks=['owned_start'])
        resolver = fragment(CALLBACKS, 'resolve_callback_fields')
        fields = [('before_model_callbacks', 'before_model_callback', 'BEFORE_MODEL'),
                  ('before_agent_callbacks', 'before_agent_callback', 'BEFORE_AGENT')]
        result = resolver(config, NS(callback_registry=None), fields)
        self.assertEqual(result, {})

    def test_unregistered_python_tool_is_not_dynamically_imported(self):
        registry = self.modules['registry'].ToolRegistry()
        registry.register('run_command', lambda: 'owned')
        resolver = fragment('adk_submission/resolvers/tools.py', 'resolve_tool_item')
        self.assertTrue(callable(resolver('run_command', NS(tool_registry=registry))))
        with self.assertRaises(self.modules['errors'].ToolNotFoundError):
            resolver('owned.module:preflight', NS(tool_registry=registry))

    def test_compiler_dispatch_and_runner_do_not_expose_factory_or_callbacks(self):
        compiler = node_at('adk_submission/compiler.py', '_compile_agent')
        types = {call.args[1].id for call in ast.walk(compiler)
                 if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
                 and call.func.id == 'isinstance' and len(call.args) == 2}
        self.assertEqual(types, {'SandboxedLlmAgentConfig', 'SandboxedSequentialAgentConfig',
                                'SandboxedParallelAgentConfig', 'SandboxedLoopAgentConfig'})
        tree = ast.parse(pinned_sources()[0]['swegemma/harness/agent_runner.py'])
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Name) and n.func.id == 'compile_submission']
        self.assertEqual(len(calls), 1)
        supplied = {k.arg for k in calls[0].keywords}
        self.assertIn('code_executor', supplied)
        self.assertNotIn('callback_registry', supplied)
        self.assertNotIn('agent_factory', supplied)


def workflow_context():
    return NS(is_resumable=False, state={'problem_description': 'OWNED_ISSUE'},
              should_pause_invocation=lambda event: getattr(event, 'pause', False),
              reset_sub_agent_states=lambda name: None)


class WorkflowInvocation(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.body = fragment(SEQUENTIAL, 'SequentialAgent._run_async_impl', {
            'Aclosing': aclosing, 'SequentialAgentState': NS})
        self.ctx = workflow_context()
        self.calls = []
        self.script_calls = 0

    def child(self, name, error=False, pause=False):
        async def run_async(ctx):
            self.calls.append((name, ctx.state['problem_description']))
            if error:
                raise RuntimeError('OWNED child failure')
            yield NS(name=name, actions=NS(escalate=False), pause=pause)
        return NS(name=name, run_async=run_async)

    async def collect(self, children):
        shell = NS(sub_agents=children, _load_agent_state=lambda *a: None,
                   _get_start_index=lambda state: 0)
        return [e async for e in self.body(shell, self.ctx)]

    async def test_sequence_schedules_pre_llm_but_does_not_require_any_script(self):
        # Each external double emits a final observation, with no tool invocation.
        events = await self.collect([self.child('diagnose'), self.child('repair')])
        self.assertEqual([e.name for e in events], ['diagnose', 'repair'])
        self.assertEqual(self.calls, [('diagnose', 'OWNED_ISSUE'), ('repair', 'OWNED_ISSUE')])
        self.assertEqual(self.script_calls, 0)

    async def test_first_child_failure_does_not_guarantee_repair_handoff(self):
        with self.assertRaisesRegex(RuntimeError, 'OWNED'):
            await self.collect([self.child('diagnose', error=True), self.child('repair')])
        self.assertEqual([n for n, _ in self.calls], ['diagnose'])

    async def test_pause_prevents_next_child(self):
        await self.collect([self.child('diagnose', pause=True), self.child('repair')])
        self.assertEqual([n for n, _ in self.calls], ['diagnose'])

    async def test_cancellation_closes_fixture_and_never_starts_repair(self):
        closed = []
        async def waiting(ctx):
            try:
                await asyncio.sleep(5)
                yield NS()
            finally:
                closed.append(True)
        with self.assertRaises(TimeoutError):
            await asyncio.wait_for(self.collect([NS(run_async=waiting), self.child('repair')]), .02)
        self.assertEqual(closed, [True])
        self.assertEqual(self.calls, [])

    async def test_loop_bounds_child_invocations_not_diagnostic_execution(self):
        body = fragment(LOOP, 'LoopAgent._run_async_impl', {'Aclosing': aclosing, 'LoopAgentState': NS})
        shell = NS(sub_agents=[self.child('diagnose')], name='owned_loop', max_iterations=3,
                   _load_agent_state=lambda *a: None, _get_start_state=lambda state: (0, 0))
        events = [e async for e in body(shell, self.ctx)]
        self.assertEqual(len(events), 3)
        self.assertEqual(self.script_calls, 0)


class SkillInvocation(unittest.IsolatedAsyncioTestCase):
    async def test_metadata_request_processing_preserves_contents_and_runs_no_script(self):
        class ListTool:
            pass
        calls = []
        body = fragment(SKILL, 'SkillToolset.process_llm_request', dict(
            ListSkillsTool=ListTool, _DEFAULT_SKILL_SYSTEM_INSTRUCTION='OWNED_METADATA'))
        contents = [dict(role='user', text='OWNED_ISSUE'), dict(role='tool', text='OWNED_CONTRADICTION')]
        req = NS(contents=contents.copy(), append_instructions=lambda items: calls.append(items))
        toolset = NS(_tools=[ListTool()], _registry=None)
        await body(toolset, tool_context=NS(), llm_request=req)
        self.assertEqual(req.contents, contents)
        self.assertEqual(calls, [['OWNED_METADATA']])

    async def test_get_tools_with_empty_activation_does_not_execute_anything(self):
        dynamic = fragment(SKILL, 'SkillToolset._resolve_additional_tools_from_state')
        toolset = NS(_tools=['list_skills', 'load_skill', 'load_skill_resource', 'run_skill_script'])
        toolset._resolve_additional_tools_from_state = lambda ctx: dynamic(toolset, ctx)
        getter = fragment(SKILL, 'SkillToolset.get_tools')
        result = await getter(toolset, NS(agent_name='owned', state={}))
        self.assertEqual(result, toolset._tools)

    async def test_explicit_script_call_routes_without_prior_list_or_load(self):
        downstream = []
        class ExecutorSpy:
            def __init__(self, executor, timeout):
                self.timeout = timeout
            async def execute_script_async(self, *args):
                downstream.append(args)
                return {'status': 'OWNED_ROUTING_ONLY'}
        async def fetch(name, invocation_id):
            return NS(resources=NS(get_script=lambda name: NS(src='PUBLIC_OWNED_FIXTURE')))
        toolset = NS(_get_or_fetch_skill=fetch, _code_executor=object(), _script_timeout=120)
        body = fragment(SKILL, 'RunSkillScriptTool.run_async', {'_SkillScriptCodeExecutor': ExecutorSpy})
        result = await body(NS(_toolset=toolset), args=dict(skill_name='owned', file_path='scripts/probe.py'),
                            tool_context=NS(invocation_id='owned', _invocation_context=NS()))
        self.assertEqual(result['status'], 'OWNED_ROUTING_ONLY')
        self.assertEqual(len(downstream), 1)
        # This routes to a spy, not a real script, sandbox, Compiler or model.

    async def test_missing_script_arguments_fail_before_execution(self):
        body = fragment(SKILL, 'RunSkillScriptTool.run_async')
        result = await body(NS(), args={}, tool_context=NS())
        self.assertEqual(result['error_code'], 'INVALID_ARGUMENTS')

    async def test_missing_executor_is_an_error_not_an_automatic_host_fallback(self):
        async def fetch(*a):
            return NS(resources=NS(get_script=lambda name: NS()))
        body = fragment(SKILL, 'RunSkillScriptTool.run_async')
        toolset = NS(_get_or_fetch_skill=fetch, _code_executor=None)
        context = NS(invocation_id='owned', _invocation_context=NS(agent=NS()))
        result = await body(NS(_toolset=toolset), args=dict(skill_name='owned', file_path='probe.py'), tool_context=context)
        self.assertEqual(result['error_code'], 'NO_CODE_EXECUTOR')


class StateAndHistoricalEvidence(unittest.TestCase):
    def test_output_key_retains_final_text_not_a_trusted_structured_contract(self):
        body = fragment('google/adk/agents/llm_agent.py', 'LlmAgent.__maybe_save_output_to_state')
        agent = NS(name='owned', output_key='receipt', output_schema=None)
        state = {'problem_description': 'OWNED_ISSUE'}
        event = NS(author='owned', is_final_response=lambda: True,
            content=NS(parts=[NS(text='{"claimed_success":true}', thought=False)]), actions=NS(state_delta={}))
        body(agent, event)
        state.update(event.actions.state_delta)
        self.assertIsInstance(state['receipt'], str)
        self.assertEqual(state['problem_description'], 'OWNED_ISSUE')

    def test_original_official_cpu_path_contains_a_real_bypass_counterexample(self):
        observations = {r['arm']: r for r in historical_bypass()['observations']}
        self.assertGreater(observations['B']['script_calls'], 0)
        self.assertEqual(observations['B_BYPASS']['script_calls'], 0)
        self.assertGreater(observations['B_BYPASS']['explicit_submit_calls'], 0)
        self.assertTrue(observations['B_BYPASS']['native_synthetic_resolved'])


class BuiltinGenerationPolicy(unittest.TestCase):
    """Existing native filters are a restricted exception, not a new projector."""
    generation = 'adk_submission/resolvers/generation.py'

    def test_pinned_competition_limits_are_executed_not_assumed(self):
        limits = schema_modules()['limits']
        tree = ast.parse(pinned_sources()[0]['swegemma/config.py'])
        scope = {name: getattr(limits, name) for name in ('SubmissionLimits', 'GenerationConstraints', 'NumericRange')}
        assignments = [n for n in tree.body if isinstance(n, ast.AnnAssign)
                       and isinstance(n.target, ast.Name) and n.target.id in (
                           'MAX_SUBMISSION_SIZE_BYTES', 'ALLOWED_SUBMISSION_EXTENSIONS', 'ALLOWED_ADAPTER_EXTENSIONS')]
        exec(compile(ast.fix_missing_locations(ast.Module(body=assignments, type_ignores=[])),
                     'swegemma/config.py:constants', 'exec'), dict(scope, __annotations__={}), scope)
        builder = fragment('swegemma/config.py', 'build_submission_limits', scope)
        structural, generation = builder()
        self.assertEqual(structural.max_agents, 500)
        self.assertEqual(structural.max_loop_iterations, 500)
        self.assertEqual(generation.defaults['max_output_tokens'], 16384)
        self.assertEqual(generation.defaults['thinking_config']['thinking_budget'], 4096)
        self.assertIn('.py', structural.allowed_file_extensions)

    def test_native_include_thoughts_configuration_is_accepted(self):
        config = schema_modules()['schema'].SandboxedAgentConfig.model_validate(dict(
            name='owned', instruction='OWNED', generate_content_config=dict(
                max_output_tokens=16384, seed=17,
                thinking_config=dict(thinking_budget=4096, include_thoughts=False)))).root
        extract = fragment(self.generation, '_extract_include_thoughts')
        self.assertIs(extract(NS(config=config.generate_content_config)), False)
        self.assertEqual(config.generate_content_config.thinking_config.thinking_budget, 4096)
        # Suppress only the SDK-installation dependency in this isolated test;
        # no Google module or Runner is modified. Execute the real mapping body.
        apply = fragment(self.generation, 'apply_thinking_config_to_model', {
            'install_litellm_reasoning_patch': lambda: True})
        original = NS(_additional_args={})
        mapped = apply(original, config.generate_content_config)
        self.assertIs(mapped._adk_include_thoughts, False)
        self.assertTrue(mapped._additional_args['extra_body']['chat_template_kwargs']['enable_thinking'])
        self.assertEqual(mapped._additional_args['extra_body']['thinking_token_budget'], 4096)
        self.assertEqual(original._additional_args, {})

    def test_native_pre_request_filter_changes_boundary_but_preserves_tool_pairs(self):
        scope = {name: fragment(self.generation, name) for name in (
            '_extract_include_thoughts', '_strip_reasoning_from_messages', '_normalize_reasoning_message')}
        enrich = fragment(self.generation,
            'install_litellm_reasoning_patch._enrich_completion_inputs', scope)
        original = [dict(role='user', content='OWNED_ISSUE'),
            dict(role='assistant', content=None, reasoning_content='OWNED_HYPOTHESIS',
                 reasoning='OWNED_HYPOTHESIS', tool_calls=[dict(id='owned-call', type='function')]),
            dict(role='tool', tool_call_id='owned-call', content='OWNED_FAILURE source=H1 patch=P1')]
        messages = copy.deepcopy(original)
        request = NS(config=NS(thinking_config=NS(include_thoughts=False), seed=17))
        result = enrich((messages, 'owned-model', None, {'max_completion_tokens': 16384}), (request,), {})
        captured = result[0]  # Owned model-boundary recorder; no model invocation.
        self.assertEqual(captured[0], original[0])
        self.assertEqual(captured[2], original[2])
        self.assertEqual(captured[1]['tool_calls'], original[1]['tool_calls'])
        self.assertNotIn('reasoning', captured[1])
        self.assertNotIn('reasoning_content', captured[1])
        self.assertEqual(result[3], dict(max_completion_tokens=16384, seed=17))

    def test_native_response_filter_cannot_preserve_question_only_in_thought(self):
        strip = fragment(self.generation, '_strip_thought_parts_from_response')
        question = NS(thought=True, text='OWNED_UNRESOLVED_QUESTION')
        tool = NS(thought=False, function_call=NS(id='owned-call'))
        response = NS(content=NS(parts=[question, tool]), partial=False, usage_metadata=None)
        filtered, skip = strip(response)
        self.assertFalse(skip)
        self.assertEqual(filtered.content.parts, [tool])
        self.assertNotIn(question, filtered.content.parts)
        again, skip = strip(filtered)
        self.assertEqual(again.content.parts, [tool])
        self.assertFalse(skip)


if __name__ == '__main__':
    unittest.main(verbosity=2)
