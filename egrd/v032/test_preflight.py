"""Offline identity/boundary/source safety tests; no generation or dispatch."""
import ast
from datetime import timedelta
from decimal import Decimal
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
import zipfile

from .prepare import HERE,ROOT,PRIVATE,BASE,S0_SHA,sha,verify_history
from .read_preflight import duration_seconds
from .observe import check_initial,InitialInputMismatch
from .source_observer import scan,Tracker
from egrd.v0311.boundary_audit import compare


class Preflight(unittest.TestCase):
    def test_historical_CPU_archive_and_frozen_inputs(self):verify_history()

    def test_quota_days_and_fractions_are_not_lost(self):
        self.assertEqual(duration_seconds(timedelta(days=1,seconds=21600,microseconds=744000)),Decimal('108000.744'))
        with self.assertRaises(AssertionError):duration_seconds(None)

    def test_original_S0_bytes_and_members(self):
        raw=(ROOT/'candidates/s0/submission.zip').read_bytes()
        self.assertEqual(sha(raw),S0_SHA)
        lock=json.loads((ROOT/'egrd/v031/S0_AGENT_LOCK.json').read_bytes())
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            self.assertEqual({n:sha(z.read(n)) for n in z.namelist()},lock['members'])

    def requests(self):
        with zipfile.ZipFile(PRIVATE/'notebook-v1/payload.zip') as z:
            return {arm:json.loads(z.read(f'egrd/v032/private/expected_{arm}.json')) for arm in ('A','B')}

    def test_first_boundary_validation_never_inserts_seed_or_overrides_output(self):
        a=self.requests()['A'];check_initial(a,a)
        b=json.loads(json.dumps(a));b['seed']=17
        with self.assertRaises(InitialInputMismatch):check_initial(b,b)
        b=json.loads(json.dumps(a));b['max_completion_tokens']=8192
        with self.assertRaises(InitialInputMismatch):check_initial(b,b)
        b=json.loads(json.dumps(a));b['messages'][0]['content']+=' unexpected guidance'
        with self.assertRaises(InitialInputMismatch):check_initial(b,a)

    def test_exact_pair_only_original_frozen_supplement(self):
        requests=self.requests()
        from egrd.v031.prepare import arm_input
        from .prepare import INPUT_PRIVATE
        original=json.loads((INPUT_PRIVATE/'original_task.json').read_bytes())['problem_statement']
        receipt=json.loads((ROOT/'egrd/v031/EVIDENCE_RECEIPT.json').read_bytes())
        suffix=arm_input(original,receipt,'B')[len(original):]
        result,_=compare(json.dumps(requests['A']).encode(),json.dumps(requests['B']).encode(),original,suffix)
        self.assertTrue(result['only_supplement_differs']);self.assertEqual(result['supplement_bytes'],1575)

    def test_actual_payload_source_closure_matches_current_runtime(self):
        build=json.loads((HERE/'BUILD.json').read_bytes())
        self.assertEqual(sha((PRIVATE/'notebook-v1/payload.zip').read_bytes()),build['payload_sha256'])
        with zipfile.ZipFile(PRIVATE/'notebook-v1/payload.zip') as z:
            self.assertIsNone(z.testzip())
            for name,digest in build['members'].items():
                self.assertEqual(sha(z.read(name)),digest,name)
                if name.startswith('egrd/v032/') and '/private/' not in name:
                    self.assertEqual((ROOT/name).read_bytes(),z.read(name),name)
            for name in ('worker.py','coordinator.py','data.py','evaluate.py'):
                body=z.read('egrd/v032/'+name)
                self.assertNotIn(b'ScriptedBoundary',body)

    def test_shared_generation_and_resource_scope(self):
        lock=json.loads((HERE/'EXPERIMENT_FREEZE.json').read_bytes())
        env=json.loads((HERE/'GPU_ENVIRONMENT_LOCK.json').read_bytes())
        self.assertEqual(lock['order'],['A','B']);self.assertEqual(lock['max_dispatches'],1);self.assertEqual(lock['max_sessions'],2)
        self.assertEqual((lock['Agent_seconds'],lock['charged_tools'],lock['command_seconds']),(300,60,120))
        self.assertIsNone(env['explicit_request_seed']);self.assertFalse(env['custom_Context_Guard'])
        self.assertIsNone(env['additional_safety_reserve']);self.assertEqual(env['generation']['max_completion_tokens'],16384)
        self.assertEqual(env['VllmConfig']['tensor_parallel_size'],4)
        self.assertEqual(env['VllmConfig']['extra_args'],['--no-enable-prefix-caching'])

    def test_VllmConfig_keywords_match_exact_official_distribution(self):
        wheel=ROOT.parent/'gemma4-swe-agent/artifacts/harness-v2/official-wheels/adk_submission-0.2.13-py3-none-any.whl'
        with zipfile.ZipFile(wheel) as z:tree=ast.parse(z.read('adk_submission/server.py'))
        definition=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='VllmConfig')
        fields={n.target.id for n in definition.body if isinstance(n,ast.AnnAssign)}
        env=json.loads((HERE/'GPU_ENVIRONMENT_LOCK.json').read_bytes())
        self.assertTrue(set(env['VllmConfig'])|{'model'}<=fields)

    def test_source_observer_detects_edit_and_does_not_claim_semantics(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);workspace=root/'workspace';(workspace/'django').mkdir(parents=True)
            source=workspace/'django/forms.py';source.write_text('value=1\n')
            rows=[]
            class Journal:
                def append(self,row):rows.append(row)
            tracker=Tracker(root/'private-observations',Journal(),scan(workspace))
            tracker.observe(workspace,0,'agent_start');source.write_text('value=1\n# inert\n')
            tracker.observe(workspace,1,'write')
            self.assertEqual(rows[-1]['changed'],['django/forms.py'])
            self.assertNotIn('meaningful_repair',rows[-1])

    def test_source_scan_does_not_follow_escape_symlink(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);workspace=root/'workspace';(workspace/'django').mkdir(parents=True)
            outside=root/'private.py';outside.write_text('PRIVATE_SENTINEL')
            try:(workspace/'django/escape.py').symlink_to(outside)
            except OSError:self.skipTest('Local OS does not permit synthetic symlink creation')
            row=scan(workspace)['django/escape.py']
            self.assertIn('symlink',row);self.assertNotIn('sha256',row)

    def test_notebook_is_private_gpu_bound_no_submission_or_readiness_generation(self):
        meta=json.loads((PRIVATE/'notebook-v1/kernel-metadata.json').read_bytes())
        self.assertTrue(meta['is_private'] and meta['enable_gpu']);self.assertFalse(meta['enable_tpu'] or meta['enable_internet'])
        self.assertEqual(meta['machine_shape'],'NvidiaL4')
        nb=json.loads((PRIVATE/'notebook-v1/study-template.ipynb').read_bytes())
        for c in nb['cells']:compile(c['source'],'<GPU-notebook>','exec')
        for name in ('coordinator.py','worker.py'):
            code=(HERE/name).read_text()
            self.assertNotIn('competitions submit',code);self.assertNotIn('seed=17',code)


if __name__=='__main__':unittest.main()
