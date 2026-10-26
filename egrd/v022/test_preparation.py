"""SCRIPTED_ONLY tool routing and owned local probes; NOT full Compiler acceptance."""
import ast
import asyncio
import json
import logging
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace as NS
import unittest
import zipfile

import yaml

from egrd.v021.interface_sources import fragment, pinned_sources, schema_modules, WHEELS
from meer.v01.build import archive, sha
from .build import HERE, original, variants, build
from .task_pool import audit_pool

SKILL='google/adk/tools/skill_toolset.py'


class CandidateIntegrity(unittest.TestCase):
    def test_rebuild_and_exact_single_member_factor(self):
        manifest=build(); files=variants(); base=original()
        for arm in ('N','D'):
            raw=archive(files[arm])
            self.assertEqual(raw,(HERE/f'submission_{arm}.zip').read_bytes())
            self.assertEqual(sha(raw),manifest['arms'][arm]['ZIP_sha256'])
            for name in base:
                if name!='prompts/system.md':self.assertEqual(files[arm][name],base[name])
            cue=(HERE/'instructions'/f'{arm}.txt').read_bytes().rstrip()
            recovered=files[arm]['prompts/system.md'].replace(b'\n\n'+cue+b'\n\n',b'\n\n',1)
            self.assertEqual(recovered,base['prompts/system.md'])
        self.assertEqual([n for n in base if files['N'][n]!=files['D'][n]],['prompts/system.md'])

    def test_real_restricted_schema_and_include_not_full_compiler(self):
        for arm,files in variants().items():
            class Loader(yaml.SafeLoader):pass
            def include(loader,node):
                name=loader.construct_scalar(node)
                self.assertEqual(name,'prompts/system.md')
                return files[name].decode()
            Loader.add_constructor('!include',include)
            config=yaml.load(files['agent.yaml'],Loader=Loader)
            actual=schema_modules()['schema'].SandboxedAgentConfig.model_validate(config).root
            self.assertEqual(actual.instruction,files['prompts/system.md'].decode())
            self.assertEqual(actual.agent_class,'LlmAgent')
            self.assertEqual(actual.skills,['skills/meer-evidence'])
            self.assertEqual(len(actual.tools),6)
            self.assertIsNone(actual.sub_agents)
            self.assertIsNone(actual.before_model_callbacks)
            self.assertEqual(actual.generate_content_config.max_output_tokens,16384)
            self.assertEqual(actual.generate_content_config.thinking_config.thinking_budget,4096)
            self.assertIsNone(actual.generate_content_config.thinking_config.include_thoughts)

    def test_no_fresh_tasks_are_fabricated_or_reservations_released(self):
        pool=audit_pool()
        self.assertEqual(pool['source_count'],129)
        self.assertEqual(pool['independent_candidates'],0)
        self.assertEqual(pool['ranked_candidates'],[])
        self.assertTrue(all(r['excluded_reasons'] for r in pool['source_record_metadata']))
        self.assertEqual(pool['new_baselines_run'],0)

    def test_tmp_probe_cannot_be_created_by_workspace_write_file_path(self):
        pinned_sources()  # Whole official wheel identities checked first.
        with zipfile.ZipFile(WHEELS/'swegemma-0.2.11-py3-none-any.whl') as z:
            source=z.read('swegemma/tools/workspace.py')
        node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef)
                  and n.name=='_resolve_workspace_path')
        namespace={'Path':Path}
        exec('from __future__ import annotations\n'+ast.unparse(node),namespace)
        with self.assertRaises(ValueError):
            namespace['_resolve_workspace_path']('/tmp/issue_check.py')


class OwnedRouting(unittest.IsolatedAsyncioTestCase):
    """Exact pinned tool/wrapper bodies; only external SDK/sandbox values doubled."""
    async def asyncSetUp(self):
        self.temp=tempfile.TemporaryDirectory();self.home=Path(self.temp.name)
        self.repo=self.home/'repo';self.repo.mkdir()
        self.source=self.repo/'logic.py';self.source.write_text('def accepts(x):\n    return x > 0\n')
        self.probe=self.home/'probe.py'
        for args in (['init','-q'],['config','user.email','owned@example.invalid'],
                     ['config','user.name','Owned'],['add','.'],['commit','-qm','owned']):
            subprocess.run(['git',*args],cwd=self.repo,check=True,capture_output=True,timeout=5)
        self.launches=0
        owner=self
        class OwnedExecutor:
            def execute_code(self,context,code_input):
                owner.launches+=1
                launch=owner.home/'owned_launcher.py';launch.write_text(code_input.code,encoding='utf-8')
                r=subprocess.run([sys.executable,str(launch)],cwd=owner.repo,
                    capture_output=True,text=True,timeout=8)
                return NS(stdout=r.stdout,stderr=r.stderr or (f'Exit {r.returncode}' if r.returncode else ''))
        # Existing original code, not a new verifier or modified Runner.
        builder=fragment(SKILL,'_SkillScriptCodeExecutor._build_wrapper_code',dict(
            _MAX_SKILL_PAYLOAD_BYTES=1_000_000,logger=logging.getLogger('owned-interface')))
        execute=fragment(SKILL,'_SkillScriptCodeExecutor.execute_script_async',dict(
            asyncio=asyncio,json=json,CodeExecutionInput=NS,logger=logging.getLogger('owned-interface')))
        class PinnedScriptExecutor:
            def __init__(self,base_executor,timeout):
                self._base_executor=base_executor;self._script_timeout=timeout
            _build_wrapper_code=builder
            execute_script_async=execute
        script=original()['skills/meer-evidence/scripts/verify.py']
        resources=NS(get_script=lambda name:NS(src=script) if name=='verify.py' else None,
            list_scripts=lambda:['verify.py'],list_references=lambda:[],list_assets=lambda:[])
        skill=NS(name='meer-evidence',resources=resources)
        self.toolset=NS(_get_skill=lambda name:skill if name=='meer-evidence' else None,
            _registry=None,_code_executor=OwnedExecutor(),_script_timeout=120)
        fetch=fragment(SKILL,'SkillToolset._get_or_fetch_skill')
        self.toolset._get_or_fetch_skill=lambda name,invocation:fetch(self.toolset,name,invocation)
        self.route=fragment(SKILL,'RunSkillScriptTool.run_async',dict(_SkillScriptCodeExecutor=PinnedScriptExecutor))
        self.context=NS(invocation_id='owned',_invocation_context=NS())

    async def asyncTearDown(self):
        # The original CLI uses a unique temporary receipt directory per repo.
        # Remove only our receipt/file and empty directory, never recursively.
        cache=Path(tempfile.gettempdir())/('meer-'+sha(str(self.repo.resolve()).encode())[:16])
        if cache.exists():
            (cache/'receipt.json').unlink(missing_ok=True)
            cache.rmdir()
        self.temp.cleanup()

    async def call(self,text=None,**overrides):
        if text is not None:self.probe.write_text(text,encoding='utf-8')
        args=dict(skill_name='meer-evidence',file_path='scripts/verify.py',
            args=dict(workspace=str(self.repo),check=str(self.probe),seconds='2'))
        args.update(overrides)
        return await self.route(NS(_toolset=self.toolset),args=args,tool_context=self.context)

    def receipt(self,response):
        self.assertIn(response['status'],('success','warning'))
        return json.loads(response['stdout'])

    async def test_direct_valid_call_has_real_source_bound_execution(self):
        r=self.receipt(await self.call('from logic import accepts\nassert accepts(1)\n'))
        self.assertEqual(r['verdict'],'SUPPORTED')
        self.assertEqual(r['executed_assertions'],1)
        self.assertEqual(len(r['source_sha256']),64)
        self.assertIsNone(r['native_resolved'])
        self.assertEqual(self.launches,1)  # No list/load call.

    async def test_required_tool_and_cli_arguments(self):
        r=await self.route(NS(_toolset=self.toolset),args={},tool_context=self.context)
        self.assertEqual(r['error_code'],'INVALID_ARGUMENTS')
        self.assertEqual(self.launches,0)
        r=await self.call(args={'workspace':str(self.repo)})
        self.assertEqual(r['status'],'error')  # --check is required by the original CLI.

    async def test_invalid_skill_and_script_identifiers(self):
        self.assertEqual((await self.call(skill_name='owned-missing'))['error_code'],'SKILL_NOT_FOUND')
        self.assertEqual((await self.call(file_path='scripts/absent.py'))['error_code'],'SCRIPT_NOT_FOUND')
        self.assertEqual(self.launches,0)

    async def test_invalid_workspace_and_absent_probe(self):
        r=self.receipt(await self.call('assert object()\n',args=dict(
            workspace=str(self.home/'absent'),check=str(self.probe),seconds='1')))
        self.assertEqual(r['verdict'],'UNKNOWN')
        self.probe.unlink()
        r=self.receipt(await self.call())
        self.assertEqual(r['verdict'],'UNKNOWN')
        self.assertEqual(r['subprocess_invocations'],0)

    async def test_assertion_free_and_constant_probe(self):
        for text in ('print("pass")\n','assert True\n'):
            r=self.receipt(await self.call(text))
            self.assertEqual(r['verdict'],'UNKNOWN')

    async def test_failed_assertion_is_local_not_native_verdict(self):
        r=self.receipt(await self.call('from logic import accepts\nassert accepts(0)\n'))
        self.assertEqual(r['exception_type'],'AssertionError')
        self.assertEqual(r['verdict'],'CONTRADICTED')
        self.assertEqual(r['semantic_correctness'],'UNKNOWN')

    async def test_dependency_and_unrelated_exception_are_not_issue_failures(self):
        for text,kind in [('import egrd_owned_missing_dep_022\n','ModuleNotFoundError'),
                          ('1/0\n','ZeroDivisionError'),('def broken(:\n','SyntaxError')]:
            r=self.receipt(await self.call(text))
            self.assertEqual(r['exception_type'],kind)
            self.assertEqual(r['verdict'],'CONTRADICTED')
            self.assertEqual(r['semantic_correctness'],'UNKNOWN')
            self.assertIsNone(r['native_resolved'])

    async def test_changed_source_invalidates_receipt_and_executes_again(self):
        text='from pathlib import Path\nassert "x > 0" in Path("logic.py").read_text()\n'
        a=self.receipt(await self.call(text));b=self.receipt(await self.call())
        self.assertEqual(b['verdict'],'OBSERVED')
        self.assertEqual(b['subprocess_invocations'],0)
        self.source.write_text('def accepts(x):\n    return x >= 0\n')
        c=self.receipt(await self.call())
        self.assertNotEqual(a['source_sha256'],c['source_sha256'])
        self.assertEqual(c['subprocess_invocations'],1)
        self.assertEqual(c['verdict'],'CONTRADICTED')

    async def test_timeout_is_unknown_and_budget_cannot_be_raised(self):
        args=dict(workspace=str(self.repo),check=str(self.probe),seconds='.1')
        r=self.receipt(await self.call('import time\ntime.sleep(5)\n',args=args))
        self.assertTrue(r['timed_out']);self.assertEqual(r['verdict'],'UNKNOWN')
        args['seconds']='16'
        r=self.receipt(await self.call(args=args))
        self.assertEqual(r['subprocess_invocations'],0)

    async def test_large_diagnostic_output_is_not_echoed_in_receipt(self):
        r=await self.call('print("X"*200000)\nassert object()\n')
        receipt=self.receipt(r)
        self.assertGreater(receipt['captured_output_bytes'],65536)
        self.assertLess(len(r['stdout']),4096)
        self.assertNotIn('X'*100,r['stdout'])
        # This proves returned receipt compactness, not a hard spool/disk limit.


if __name__=='__main__':unittest.main(verbosity=2)
