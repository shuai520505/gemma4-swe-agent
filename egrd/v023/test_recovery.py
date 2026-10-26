"""Offline source/result regressions; never submit a Notebook or call a model."""
import copy
import io
import json
import subprocess
import tarfile
import unittest
import zipfile

from jsonschema import Draft202012Validator, ValidationError

from .cli_recovery import HERE, ROOT, PRIVATE, REF, sha
from .cpu_acceptance import HASHES, actions


class Recovery(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results=json.loads((HERE/'CPU_TEST_RESULTS.json').read_bytes())
        cls.source=json.loads((HERE/'EXTERNAL_SOURCE_LOCK.json').read_bytes())
        cls.execution=json.loads((HERE/'KAGGLE_EXECUTION_RECORD.json').read_bytes())
        cls.raw=(PRIVATE/'v1-output/egrd-v023-cpu-v1.zip').read_bytes()

    def test_actual_raw_archive_identity_and_crc(self):
        self.assertEqual(sha(self.raw),self.results['archive_sha256'])
        with zipfile.ZipFile(io.BytesIO(self.raw)) as z:
            self.assertIsNone(z.testzip())
            build=json.loads((HERE/'cpu-v1/BUILD.json').read_bytes())
            for name,digest in build['payload_members'].items():
                self.assertEqual(sha(z.read('source/'+name)),digest,name)

    def test_frozen_candidates_and_only_prompt_difference(self):
        packages={}
        for arm,digest in HASHES.items():
            body=(ROOT/f'egrd/v022/submission_{arm}.zip').read_bytes()
            self.assertEqual(sha(body),digest)
            with zipfile.ZipFile(io.BytesIO(body)) as z:
                packages[arm]={n:z.read(n) for n in z.namelist()}
        self.assertEqual([n for n in packages['N'] if packages['N'][n]!=packages['D'][n]],['prompts/system.md'])
        self.assertEqual(sha(packages['N']['skills/meer-evidence/scripts/verify.py']),
            'dae959c8068e6d320c7fc5c37f719ccd928f56dd19f4335af0d33193ea3f499c')

    def test_full_real_sdk_versions_and_generation(self):
        self.assertEqual(self.results['SDK'],{'swegemma':'0.2.11','adk-submission':'0.2.13',
            'google-adk':'1.36.1','adk-eval-core':'0.1.0'})
        for r in self.results['records']:
            self.assertTrue(r['full_compiler'])
            self.assertEqual(r['generation'],dict(max_output_tokens=16384,seed=17,thinking_config=dict(thinking_budget=4096)))
            self.assertIn('SkillToolset',r['compiled_tool_entries'])

    def test_no_model_or_accelerator_and_once_only_cpu(self):
        self.assertEqual(self.execution['versions_executed'],1)
        self.assertEqual(self.execution['ref'],REF)
        self.assertEqual(self.execution['GPU_devices_observed'],0)
        self.assertEqual(self.execution['actual_Gemma_requests'],0)
        self.assertFalse((PRIVATE/'dispatch-v2.json').exists())
        meta=json.loads((PRIVATE/'actual-v1-pull/kernel-metadata.json').read_bytes())
        self.assertTrue(meta['is_private'])
        self.assertFalse(meta['enable_gpu'] or meta['enable_tpu'] or meta['enable_internet'])
        self.assertEqual(meta['model_sources'],[])

    def test_scripted_boundary_is_not_real_token_evidence(self):
        self.assertEqual(self.results['CPU_MODEL'],'SCRIPTED_ONLY')
        self.assertIsNone(self.results['real_model_token_usage'])
        self.assertEqual(self.results['scripted_HTTP_requests'],44)
        self.assertEqual(sum(isinstance(x,tuple) and x[0]=='run_skill_script' for x in actions()),14)

    def test_source_bound_failure_pass_and_repeat(self):
        for r in self.results['records']:
            before,after,repeat=r['local_receipts'][-3:]
            self.assertEqual((before['verdict'],after['verdict'],repeat['verdict']),('CONTRADICTED','SUPPORTED','OBSERVED'))
            self.assertNotEqual(before['source_sha256'],after['source_sha256'])
            self.assertEqual(repeat['subprocess_invocations'],0)
            self.assertTrue(r['direct_without_list_load'])

    def test_negative_checks_are_not_issue_success(self):
        for r in self.results['records']:
            receipts=r['local_receipts']
            self.assertEqual([v['exception_type'] for v in receipts[3:6]],['ModuleNotFoundError','SyntaxError','ValueError'])
            self.assertTrue(receipts[6]['timed_out'])
            self.assertEqual(receipts[6]['verdict'],'UNKNOWN')
            for receipt in receipts:
                self.assertIsNone(receipt['native_resolved'])
                self.assertEqual(receipt['semantic_correctness'],'UNKNOWN')

    def test_actual_native_synthetic_and_cleanup(self):
        for r in self.results['records']:
            self.assertTrue(r['synthetic_native_resolved'] and r['explicit_submit'])
            self.assertTrue(r['cleanup']['complete'] and r['cleanup']['owned_roots_removed'])
            self.assertEqual(r['skill_responses'],14)
            self.assertEqual(r['charged_tools'],17)

    def test_json_schema_and_negative_case(self):
        schema=json.loads((HERE/'CPU_TEST_RESULTS.schema.json').read_bytes())
        Draft202012Validator.check_schema(schema)
        validator=Draft202012Validator(schema);validator.validate(self.results)
        altered=copy.deepcopy(self.results);altered['real_model_token_usage']=0
        with self.assertRaises(ValidationError):validator.validate(altered)

    def test_same_official_source_and_exclusions(self):
        original=(ROOT.parent/'official-inputs/tasks.jsonl').read_bytes()
        current=(PRIVATE/'official-current/tasks.jsonl').read_bytes()
        self.assertEqual(current,original)
        pool=json.loads((ROOT/'egrd/v022/TASK_POOL_LOCK.json').read_bytes())
        self.assertEqual(pool['independent_candidates'],0)
        self.assertEqual(len(current.splitlines()),129)
        self.assertEqual(len(json.loads((PRIVATE/'competition_files.json').read_bytes())),524)

    def test_external_publisher_hash_and_projection(self):
        self.assertEqual(self.source['task_count'],500)
        self.assertEqual(self.source['repository_disjoint_count'],492)
        for name,record in self.source['files'].items():
            self.assertEqual(record['sha256'],record['publisher_LFS_sha256'])
            self.assertEqual(sha((PRIVATE/'external-sources'/name.split('/')[-1]).read_bytes()),record['sha256'])
        self.assertFalse(self.source['official_native_compatible'])
        self.assertFalse(self.source['docker']['binary_present'])

    def test_external_ranking_and_snapshot_without_admission(self):
        rows=self.source['ranked_metadata'];prefix=self.source['ranking_prefix']
        self.assertEqual(rows,sorted(rows,key=lambda r:(sha((prefix+r['instance_id']).encode()),r['instance_id'])))
        checks=json.loads((HERE/'EXTERNAL_SNAPSHOT_CHECKS.json').read_bytes())
        self.assertEqual([r['instance_id'] for r in checks['records']],[r['instance_id'] for r in rows[:2]])
        self.assertEqual(checks['admitted_count'],0)
        for r in checks['records']:
            raw=(PRIVATE/'external-sources/snapshots'/f"{r['instance_id']}.tgz").read_bytes()
            self.assertEqual(sha(raw),r['snapshot_sha256'])
            with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as z:
                for name,digest in r['license_file_hashes'].items():
                    self.assertEqual(sha(z.extractfile(r['archive_root']+'/'+name).read()),digest)

    def test_historical_022_files_unchanged(self):
        manifest=json.loads((ROOT/'egrd/v022/INTEGRITY_MANIFEST.json').read_bytes())
        for name,record in manifest['files'].items():
            self.assertEqual(sha((ROOT/'egrd/v022'/name).read_bytes()),record['sha256'],name)
        self.assertEqual(subprocess.check_output(['git','diff','e11b28c99bec91049aec68119fead5e13fa68373','--','egrd/v022','meer/v01','submission.zip'],cwd=ROOT),b'')


if __name__=='__main__':unittest.main()
