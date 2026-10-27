"""Offline artifact and engineering-result regressions; no API/model calls."""
import ast
import io
import json
from pathlib import Path
import unittest
import zipfile
import subprocess
import stat

from .prepare import HERE,ROOT,PRIVATE,PRIOR_PRIVATE,S0_SHA,sha,arm_input


class Preparation(unittest.TestCase):
    def test_namespace_and_frozen_history_unchanged(self):
        changed=subprocess.check_output(['git','diff','--name-only','5829838066b5c3cfb3037ebbf2613011c2d4f214'],cwd=ROOT,text=True).splitlines()
        self.assertTrue(all(n.startswith('egrd/v031/') for n in changed),changed)
        for arm,digest in dict(N='c0618f4a996883600b1353a7a7e5fe0d8588f4393613984f30f725b4cfa98e69',
            D='253002dcea2f077945aebacee3c9ea3a6033601aedcf4b55964d99fe8b5b09d7').items():
            self.assertEqual(sha((ROOT/f'egrd/v022/submission_{arm}.zip').read_bytes()),digest)

    def test_original_S0_zip_and_all_members(self):
        path=ROOT/'candidates/s0/submission.zip'
        manifest=json.loads((ROOT/'candidates/s0/manifest.json').read_bytes())
        self.assertEqual(sha(path.read_bytes()),S0_SHA)
        with zipfile.ZipFile(path) as z:
            self.assertIsNone(z.testzip())
            self.assertEqual({n:sha(z.read(n)) for n in z.namelist()},manifest['source_hashes'])
            self.assertEqual(set(z.namelist()),{'agent.yaml','eval_config.yaml','prompts/system.md'})

    def test_original_issue_and_exact_supplement_only(self):
        task=json.loads((PRIVATE/'original_task.json').read_bytes())
        lock=json.loads((HERE/'TASK_IDENTITY_LOCK.json').read_bytes())
        receipt=json.loads((HERE/'EVIDENCE_RECEIPT.json').read_bytes())
        original=task['problem_statement'];a=arm_input(original,receipt,'A');b=arm_input(original,receipt,'B')
        self.assertEqual(sha(original.encode()),lock['issue_sha256'])
        self.assertEqual(a,original);self.assertTrue(b.startswith(original))
        self.assertEqual(b.count(original),1)
        self.assertNotIn('<EGRD_DEVELOPMENT_OBSERVATION>',a)
        self.assertIn('<EGRD_DEVELOPMENT_OBSERVATION>',b)

    def test_receipt_original_result_and_source_bound(self):
        public=json.loads((HERE/'EVIDENCE_RECEIPT.json').read_bytes())
        lock=json.loads((HERE/'TASK_IDENTITY_LOCK.json').read_bytes())
        with zipfile.ZipFile(PRIOR_PRIVATE/'output-v1/egrd-v03-cpu-v1.zip') as z:
            raw=json.loads(z.read('results/tasks/django__django-16333/RESULT.json'))
        self.assertEqual(public['tested_source_tree_sha256'],raw['source_tree_before'])
        self.assertEqual(public['diagnostic_program_sha256'],raw['probe_sha256'])
        self.assertEqual(public['original_receipt_sha256'],lock['probe_receipt_sha256'])
        self.assertEqual(public['observed_related_count'],raw['probe']['checks'][-1]['actual'])
        self.assertEqual(public['expected_related_count'],1)
        self.assertEqual(public['positive_control_assertions_passed'],3)
        self.assertEqual(public['target_assertions_failed'],1)
        self.assertIsNone(public['official_native_resolved'])
        self.assertFalse({'patch','test_patch','solution','root_cause','suggested_modification'} & set(public))

    def test_sealed_exact_cpu_payload(self):
        version=json.loads((HERE/'CPU_TEST_RESULTS.json').read_bytes())['CPU_Notebook_version']
        build=json.loads((HERE/f'CPU_BUILD_V{version}.json').read_bytes())
        folder=PRIVATE/f'notebook-v{version}'
        self.assertEqual(sha((folder/'study.ipynb').read_bytes()),build['Notebook_sha256'])
        self.assertEqual(sha((folder/'payload.zip').read_bytes()),build['payload_sha256'])
        with zipfile.ZipFile(folder/'payload.zip') as z:
            self.assertIsNone(z.testzip())
            for n,h in build['members'].items():self.assertEqual(sha(z.read(n)),h,n)
            self.assertEqual(sha(z.read('candidates/s0/submission.zip')),S0_SHA)
        meta=json.loads((folder/'kernel-metadata.json').read_bytes())
        self.assertTrue(meta['is_private']);self.assertFalse(meta['enable_gpu'])
        self.assertFalse(meta['enable_tpu']);self.assertFalse(meta['enable_internet'])
        self.assertFalse(meta['model_sources']);self.assertFalse(meta['competition_sources'])

    def test_inert_fixture_edits_preserve_ast(self):
        import tarfile
        with zipfile.ZipFile(PRIOR_PRIVATE/'dataset-v1/data_bundle.zip') as z:
            with tarfile.open(fileobj=io.BytesIO(z.read('snapshots/django__django-16333.tgz')),mode='r:gz') as t:
                body=t.extractfile('django-60a7bd89860e504c0c33b02c78edcac87f6d1b5a/django/contrib/auth/forms.py').read().decode()
        replacement='import unicodedata\n# EGRD_SCRIPTED_ONLY_TRANSPORT_MARKER: inert engineering comment, no repair.\n'
        changed=body.replace('import unicodedata\n',replacement)
        self.assertNotEqual(body,changed)
        self.assertEqual(ast.dump(ast.parse(body)),ast.dump(ast.parse(changed)))

    def test_actual_blocked_cpu_gate_records(self):
        cpu=json.loads((HERE/'CPU_TEST_RESULTS.json').read_bytes())
        self.assertEqual(cpu['status'],'CPU_PREFLIGHT_BLOCKED')
        self.assertEqual(cpu['CPU_MODEL'],'SCRIPTED_ONLY');self.assertEqual(cpu['real_Gemma_requests'],0)
        self.assertEqual([r['arm'] for r in cpu['records']],['A','B'])
        a,b=cpu['records']
        self.assertTrue(a['full_compiler'] and a['native_Runner_initialized'] and a['agent_cleanup'])
        self.assertEqual(a['package_sha256'],S0_SHA)
        self.assertFalse(a['successful_submit']);self.assertIn('/dev/null',a['submit_error'])
        self.assertIsNone(a['actual_model_tokens']);self.assertIsNone(a['official_native_resolved'])
        self.assertEqual(b['status'],'NOT_RUN');self.assertIsNone(b['full_compiler'])
        self.assertTrue(cpu['baseline']['original_failing_probe_still_fails'])
        self.assertTrue(cpu['baseline']['trusted_probe_write_denied'])
        self.assertEqual(cpu['baseline']['bounded_regression_exit_code'],0)

    def test_boundary_and_future_experiment_stop(self):
        audit=json.loads((HERE/'CPU_TEST_RESULTS.json').read_bytes())['input_boundary']
        self.assertIsNone(audit['only_B_has_receipt']);self.assertIsNone(audit['original_issue_exact'])
        self.assertIsNone(audit['instructions_equal']);self.assertIsNone(audit['tools_equal'])
        self.assertIsNone(audit['token_overhead'])
        gpu=json.loads((HERE/'GPU_EXECUTION_LOCK.json').read_bytes())
        self.assertFalse(gpu['execution_frozen']);self.assertFalse(gpu['GPU_authorized'])
        self.assertTrue(all(s['status']=='NOT_RUN' and s['official_native_resolved'] is None for s in gpu['sessions']))
        self.assertEqual([(s['task_id'],s['arm']) for s in gpu['sessions']],
                         [('django__django-16333','A'),('django__django-16333','B')])

    def test_null_device_requires_real_character_device(self):
        self._null_case('success')

    def test_null_device_permission_failure_has_no_regular_fallback(self):
        self._null_case('permission')

    def test_null_device_rejects_regular_file_result(self):
        self._null_case('regular')

    def _null_case(self,case):
        from types import SimpleNamespace
        from unittest.mock import patch
        from . import device_runtime
        class Node:
            present=True;mode=stat.S_IFREG|0o666;rdev=0;chmod_calls=0
            def is_symlink(self):return False
            def exists(self):return self.present
            def unlink(self):self.present=False
            def chmod(self,value):self.chmod_calls+=1
            def stat(self):return SimpleNamespace(st_mode=self.mode,st_rdev=self.rdev)
        node=Node()
        class Root:
            def __truediv__(self,value):
                assert value=='dev/null';return node
        calls=[]
        def create(path,mode,device):
            calls.append((path,mode,device))
            if case=='permission':raise PermissionError('Synthetic CAP_MKNOD unavailable')
            node.present=True;node.mode=mode if case=='success' else stat.S_IFREG|0o666;node.rdev=device
        with patch.object(device_runtime.os,'mknod',create,create=True),patch.object(device_runtime.os,'makedev',lambda a,b:(a<<8)|b,create=True):
            if case=='success':
                proof=device_runtime.install_null_device(Root())
                self.assertEqual(proof,dict(kind='CHAR_DEVICE',major=1,minor=3,regular_file_fallback=False))
            else:
                with self.assertRaises(PermissionError if case=='permission' else AssertionError):
                    device_runtime.install_null_device(Root())
        self.assertEqual(len(calls),1)
        if case=='permission':self.assertFalse(node.present);self.assertEqual(node.chmod_calls,0)


if __name__=='__main__':unittest.main()
