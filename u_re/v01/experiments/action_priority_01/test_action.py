import copy
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
import yaml
from .build import HERE, BASE, frozen, PINS, sha
from .metrics import summarize


class ActionTests(unittest.TestCase):
    def test_exact_single_insertion_and_archives(self):
        original=frozen()['noegv'];audit=json.loads((HERE/'CANDIDATE_AUDIT.json').read_text())
        zpath=HERE/'submission_action_v01.zip'
        self.assertEqual(sha(zpath.read_bytes()),audit['zip_sha256'])
        with zipfile.ZipFile(zpath) as z:
            self.assertIsNone(z.testzip());self.assertEqual(set(z.namelist()),set(original))
            for n in original:
                b=z.read(n);self.assertEqual(b,(HERE/'candidate_action_v01'/n).read_bytes())
                if n!='prompts/system.md':self.assertEqual(b,original[n])
            block=(HERE/'ACTION_FIRST_INSTRUCTION_BLOCK.md').read_bytes()
            self.assertEqual(z.read('prompts/system.md').replace(block+b'\n',b'',1),original['prompts/system.md'])
            self.assertEqual(len(block.decode().split()),119)
    def test_config_and_include(self):
        # Local structural loader only; official loader is tested separately on CPU.
        class Loader(yaml.SafeLoader): pass
        Loader.add_constructor('!include',lambda loader,node:dict(include=loader.construct_scalar(node)))
        agent=yaml.load((HERE/'candidate_action_v01/agent.yaml').read_bytes(),Loader=Loader)
        self.assertEqual(agent['instruction'],dict(include='prompts/system.md'))
        self.assertEqual(agent['model'],'gemma-4-31b-it-qat-w4a16-ct')
        self.assertEqual(agent['agent_class'],'LlmAgent')
        self.assertEqual(set(agent['tools']),{'get_status','read_file','edit_file','write_file','run_command','submit_patch'})
        self.assertEqual(len(agent['tools']),6);self.assertNotIn('sub_agents',agent)
        budget=yaml.safe_load((HERE/'candidate_action_v01/eval_config.yaml').read_bytes())['evaluation']
        self.assertEqual(budget,dict(timeout_seconds=120,max_tool_calls=60,max_time_minutes=5.0))
    def test_guards_remain_and_no_egv_treatment(self):
        prompt=(HERE/'candidate_action_v01/prompts/system.md').read_text()
        for required in ('Correctness takes priority','Run relevant ordinary tests','Do not alter protected tests',
                         'After a successful submit_patch','Never repeat a successful submission','unsupported self-authored expectation'):
            self.assertIn(required,prompt)
        self.assertNotIn('Evidence-gated verification:',prompt)
        self.assertNotIn('{',prompt);self.assertNotIn('}',prompt)
        for forbidden in ('fastapi_','rich_','requests_','httpx_','reference_patch','test_patch','agent_tool'):
            self.assertNotIn(forbidden,prompt)
    def run_fixture(self):
        def e(t,kind,**kwargs):return dict(seconds=t,kind=kind,raw_event_id=str(t),raw_artifact_sha256='a'*64,**kwargs)
        events=[e(10,'file_change',path_class='scratch',before_sha256='b'*64,after_sha256='c'*64),
            e(20,'file_change',path_class='production',before_sha256='b'*64,after_sha256='c'*64),
            e(25,'patch',bytes=30,applies_cleanly=True,diff_check_exit=0,production_paths=['src/toy.py'],patch_sha256='d'*64,source_tree_sha256='e'*64),
            e(30,'check',check_id='target',patch_sha256='d'*64,source_tree_sha256='e'*64,workspace_source_proven=True,assertions_executed=True,exit_code=0),
            e(40,'tool_response',name='submit_patch',status='ok',patch_sha256='d'*64),
            e(41,'tool_call',name='run_command'),e(42,'tool_response',name='submit_patch',status='ok',patch_sha256='d'*64),
            e(45,'model_request',usage=dict(prompt_tokens=50,completion_tokens=7)),e(46,'model_request',usage=None)]
        return dict(schema_version=1,status='timeout',native_resolved=None,events=events,model_request_capture_complete=True,
            registered_target_check_ids=['target'],final_patch_bytes=30,agent_wall_seconds=300,worker_wall_seconds=410)
    def test_metrics_true_edit_patch_support_and_partial_usage(self):
        result=summarize(self.run_fixture())
        self.assertEqual(result['time_to_first_source_edit'],20)
        self.assertEqual(result['time_to_first_applicable_patch'],25)
        self.assertEqual(result['time_to_first_locally_supported_patch'],30)
        self.assertIsNone(result['resolved']);self.assertIsNone(result['prompt_tokens'])
        self.assertEqual(result['received_prompt_tokens_partial'],50)
        self.assertEqual(result['post_submit_tool_calls'],1);self.assertEqual(result['identical_successful_resubmits'],1)
    def test_wrong_source_or_unproven_assertion_not_valid_patch(self):
        fixture=self.run_fixture();fixture['events'][3]['source_tree_sha256']='f'*64
        self.assertIsNone(summarize(fixture)['time_to_first_locally_supported_patch'])
        fixture=self.run_fixture();fixture['events'][3]['assertions_executed']=False
        self.assertIsNone(summarize(fixture)['time_to_first_locally_supported_patch'])
        fixture=self.run_fixture();fixture['events'][2].pop('source_tree_sha256');fixture['events'][3].pop('source_tree_sha256')
        self.assertIsNone(summarize(fixture)['time_to_first_locally_supported_patch'])
    def test_repeated_failure_is_review_candidate_not_automatic_agent_failure(self):
        f=self.run_fixture();f['events']=[]
        for t in (1,2):
            f['events'].append(dict(seconds=t,kind='operation',operation_class='test',raw_event_id=str(t),raw_artifact_sha256='a'*64,
                **{n:'b'*64 for n in ('command_sha256','source_tree_sha256','input_sha256','environment_sha256','result_sha256')}))
        self.assertEqual(summarize(f)['repeated_unchanged_test_candidates'],1)
        f['events'][1]['source_tree_sha256']='c'*64
        self.assertEqual(summarize(f)['repeated_unchanged_test_candidates'],0)
    def test_not_run_and_unbacked_events_do_not_turn_into_zero_or_success(self):
        f=dict(schema_version=1,status='not_run',native_resolved=None,events=None)
        self.assertIsNone(summarize(f)['event_metrics'])
        f=self.run_fixture();f['events'][1]['raw_artifact_sha256']='not proven'
        r=summarize(f);self.assertIsNone(r['time_to_first_source_edit']);self.assertEqual(r['unbacked_events'],1)
    def test_missing_request_capture_is_unknown_and_resubmits_not_pair_counted(self):
        f=self.run_fixture();f.pop('model_request_capture_complete')
        r=summarize(f);self.assertIsNone(r['total_model_requests']);self.assertIsNone(r['prompt_tokens'])
        f=self.run_fixture();e=copy.deepcopy(f['events'][6]);e['seconds']=43;f['events'].insert(7,e)
        self.assertEqual(summarize(f)['identical_successful_resubmits'],2)
        f=self.run_fixture();f['events'][5]['seconds']=40
        self.assertEqual(summarize(f)['post_submit_tool_calls'],1)
        f=self.run_fixture();f['events'][-2]['usage']={'prompt_tokens':None,'completion_tokens':None}
        self.assertIsNone(summarize(f)['received_prompt_tokens_partial'])
    def test_selection_is_prospective_deterministic_and_cannot_relax_exclusions(self):
        from .selection import rank
        rows=[dict(instance_id=i,repo='owned/toy') for i in ('owned_one','owned_two','fastapi_14262')]
        a=rank(rows,{'owned_reserved'},{'owned_reserved'})
        self.assertEqual(a,rank(list(reversed(rows)),{'owned_reserved'},{'owned_reserved'}))
        self.assertNotIn('fastapi_14262',[r['instance_id'] for r in a])
        with self.assertRaises(ValueError):rank(rows,{'owned_reserved'},set())
        with self.assertRaises(ValueError):rank([dict(instance_id='owned',resolved=True)],set(),set())


if __name__=='__main__':unittest.main(verbosity=2)
