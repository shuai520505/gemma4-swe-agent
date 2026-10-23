"""Owned classification cases and SaveKernel guards; no SWE/model execution."""
import ast,json,unittest
from unittest.mock import patch
from .dependencies import HERE,sha
from .policy import classify,event_class
from .notebook import factory,validate_attempt

class Categories(unittest.TestCase):
    def setUp(self):
        self.row=dict(evidence_ok=True,counts=dict(tests=1,failures=0,errors=1))
        self.source={'requirements-tests.txt':dict(text='inline-snapshot>=0.21.1\nowned-missing>=1\n'), 'fastapi/exceptions.py':dict(text='class OwnedExisting(Exception): pass\n',sha256='owned'), 'fastapi/param_functions.py':dict(text='def Depends(dependency=None): pass\n',sha256='owned')}
    def test_A_requires_observed_absence_not_unknown_dict_key(self):
        e=dict(details="ModuleNotFoundError: No module named 'owned_missing'")
        self.assertEqual(event_class(e,self.source,'Owned behavior',{})[0],'D')
        self.assertEqual(event_class(e,self.source,'Owned behavior',{'owned-missing':None})[0],'A')
    def test_unknown_unrelated_missing_is_STOP(self):
        self.assertEqual(event_class(dict(details="ModuleNotFoundError: No module named 'undeclared_owned'"),self.source,'Owned',{'undeclared-owned':None})[0],'D')
    def test_target_keyword_needs_issue_and_frozen_signature(self):
        e=dict(details="TypeError: Depends() got an unexpected keyword argument 'scope'")
        self.assertEqual(event_class(e,self.source,'Add Depends scope support',{})[0],'B')
        self.assertEqual(event_class(e,self.source,'Unrelated change',{})[0],'D')
    def test_target_exception_is_conditional_never_formal(self):
        e=dict(details="ImportError: cannot import name 'PydanticV1NotSupportedError' from 'fastapi.exceptions' (/workspace/fastapi/exceptions.py)")
        k,p=event_class(e,self.source,'Drop pydantic.v1 support, raise error',{})
        self.assertEqual(k,'B');self.assertFalse(p['formal_admission']);self.assertFalse(p['Issue_spells_exact_API'])
    def test_mixed_known_environment_and_target_reject_continue(self):
        events=[dict(category='collection_error',details="ModuleNotFoundError: No module named 'inline_snapshot'"),dict(category='collection_error',details="TypeError: Depends() got an unexpected keyword argument 'scope'")]
        d=classify(self.row,dict(category='collection_error',events=events),self.source,'Add Depends scope support',{'inline-snapshot':None})
        self.assertEqual(d['category'],'C');self.assertEqual(d['status'],'REJECT_CONTINUE');self.assertFalse(d['eligible'])
    def test_unknown_mixed_failure_stops(self):
        events=[dict(category='collection_error',details="ModuleNotFoundError: No module named 'inline_snapshot'"),dict(category='collection_error',details='owned unclassified failure')]
        d=classify(self.row,dict(category='collection_error',events=events),self.source,'Owned',{'inline-snapshot':None})
        self.assertEqual(d['category'],'D');self.assertEqual(d['status'],'STOP');self.assertIsNone(d['eligible'])
    def test_integrity_overrides_behavior_failure(self):
        d=classify(dict(self.row,evidence_ok=False),dict(category='assertion_failure'),self.source,'Owned',{})
        self.assertEqual(d['category'],'E');self.assertEqual(d['status'],'STOP')

class Dispatch(unittest.TestCase):
    def test_actual_recovery_zip_all_hashes_and_assets(self):self.assertTrue(validate_attempt('recovery01'))
    def test_precheck_failure_cannot_reach_auth_or_save(self):
        m=factory('recovery01')
        with patch(__package__+'.notebook.validate_attempt',side_effect=ValueError('OWNED_PRECHECK_FAILURE')):
            # factory clones the function's globals; patch its explicit guard.
            m.launch.__globals__['validate_attempt']=lambda _:(_ for _ in ()).throw(ValueError('OWNED_PRECHECK_FAILURE'))
            with self.assertRaisesRegex(ValueError,'OWNED_PRECHECK_FAILURE'):m.launch()
    def test_carry_and_order_decided_before_new_outcomes(self):
        p=json.loads((HERE/'TASK_POOL_FREEZE.json').read_bytes())
        self.assertEqual(p['carry'],'fastapi_5077');self.assertEqual(len(p['ranked_rows']),29);self.assertEqual(len(p['next_max24_in_order']),24)
        self.assertEqual(len(p['inherited_excluded_ids']),95)
        self.assertTrue(set(p['prior_observed_ids']).isdisjoint({r['instance_id'] for r in p['ranked_rows']}))

class SnapshotPhases(unittest.TestCase):
    def raw(self,message=None):
        import xml.etree.ElementTree as ET
        from .junit_audit import MESSAGE
        root=ET.Element('testsuites');suite=ET.SubElement(root,'testsuite',tests='1',failures='1',errors='1',skipped='0')
        case=ET.SubElement(suite,'testcase',classname='owned',name='test_owned')
        ET.SubElement(case,'failure',message='assert 2 == 1').text='assert 2 == snapshot(1)'
        case=ET.SubElement(suite,'testcase',classname='owned',name='test_owned')
        ET.SubElement(case,'error',message='failed on teardown with "Failed: '+(message or MESSAGE)+'"').text=message or MESSAGE
        return ET.tostring(root)
    def test_expected_teardown_duplicate_preserves_real_failure_and_error(self):
        from .junit_audit import parse_snapshot_phases
        d=parse_snapshot_phases(self.raw())
        self.assertEqual(d['counts'],dict(tests=1,failures=1,errors=1,skipped=0));self.assertEqual(d['JUnit_records'],2)
        self.assertTrue(d['confirmed_failure']);self.assertFalse(d['infrastructure_stop'])
    def test_independent_teardown_error_cannot_be_hidden(self):
        from .junit_audit import parse_snapshot_phases
        with self.assertRaises(AssertionError):parse_snapshot_phases(self.raw('owned unrelated fixture crash'))
    def test_corrupt_aggregate_cannot_be_hidden(self):
        from .junit_audit import parse_snapshot_phases
        with self.assertRaises(AssertionError):parse_snapshot_phases(self.raw().replace(b'tests="1"',b'tests="999"'))

class Production(unittest.TestCase):
    def test_new_GPU_route_requires_matching_authorization_before_environment_or_model(self):
        import asyncio
        from .production.session import run
        with self.assertRaisesRegex(AssertionError,'GPU NOT_AUTHORIZED'):
            asyncio.run(run('OWNED_NOT_CREATED',0,mode='GPU'))
    def test_real_GPU03_coordinator_adapts_without_rewriting_worker(self):
        from .production.session import adapted_session
        lock=json.loads((HERE/'production/ABBA_EXPERIMENT_LOCK.json').read_bytes())
        grant=json.loads((HERE/'production/GPU_AUTHORIZATION.json').read_bytes())
        f=adapted_session(lock,grant)
        self.assertEqual(len(f.__globals__['V02B_LOCK']['tasks']),4)
        self.assertEqual(f.__globals__['__package__'],'u_re.v01.experiments.action_priority_01.real_gemma_abba03')
        self.assertEqual([r['arm'] for r in lock['order']],list('ABBAABBA'))
    def test_production_precheck_failure_precedes_auth_and_dispatch(self):
        from .production_notebook import factory
        m=factory('e2e01')
        m.launch.__globals__['validate']=lambda _:(_ for _ in ()).throw(ValueError('OWNED_FINAL_PAYLOAD_INVALID'))
        with self.assertRaisesRegex(ValueError,'OWNED_FINAL_PAYLOAD_INVALID'):m.launch()
    def test_final_payload_and_all_frozen_files_validate(self):
        from .production_notebook import validate
        self.assertTrue(validate('e2e02'))
    def test_GPU_route_rejects_scripted_transport_even_with_claimed_authorization(self):
        import asyncio
        from .production.session import run
        with self.assertRaisesRegex(AssertionError,'Scripted transport forbidden'):
            asyncio.run(run('OWNED_NOT_CREATED',0,mode='GPU',cpu_transport=object(),authorization={'GPU_authorized':True}))

class ActualEvidence(unittest.TestCase):
    def test_final_CPU_acceptance_is_rederived_from_exact_private_raw_archive(self):
        from .production_audit import audit
        proof=json.loads((HERE/'CPU_END_TO_END_ACCEPTANCE.json').read_bytes())
        self.assertEqual(audit(proof['raw_archive_path'],proof['attempt']),proof)
    def test_prospective_prefix_and_carry_are_not_relabelled_as_four_new(self):
        ledger=json.loads((HERE/'TASK_ADMISSION_LEDGER.json').read_bytes())
        selected=json.loads((HERE/'SELECTED_TASKS.json').read_bytes())
        self.assertEqual((ledger['checked_new'],selected['carry_count'],selected['new_count']),(3,1,3))
        self.assertEqual([r['instance_id'] for r in ledger['rows'][:3]],['fastapi_11355','fastapi_14463','fastapi_9555'])
        self.assertTrue(all(r['status']=='NOT_RUN' for r in ledger['rows'][3:]))
        self.assertEqual(len(selected['tasks']),4)
    def test_screened_environment_and_protocol_files_remain_frozen(self):
        p=json.loads((HERE/'V02B_PROTOCOL_LOCK.json').read_bytes())
        self.assertEqual(sha((HERE/'V02B_ENVIRONMENT_LOCK.json').read_bytes()),p['environment_lock_sha256'])
        for name,h in p['execution_sources'].items():self.assertEqual(sha((HERE/name).read_bytes()),h)

if __name__=='__main__':unittest.main()
