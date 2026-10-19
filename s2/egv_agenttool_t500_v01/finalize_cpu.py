"""Composite acceptance with explicit failed-preparation provenance, no log rewriting."""
import json
from pathlib import Path
from experiments.prepare import write_new
from s1.util import sha_file
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def main(revision='cpu04'):
    prior=HERE/'results/cpu03/validation'
    log=(prior/'new_tests.log').read_text()
    good=[line for line in log.splitlines() if line.startswith('test_') and line.endswith(' ... ok')]
    assert len(good)==8
    old=json.loads((prior/'new_gate.json').read_text())
    assert not old['passed'] and old['test_methods']==9 and old['errors']==1 and old['failures']==0
    assert "missing 2 required positional arguments: 'submission_dir' and 'models'" in log
    native=json.loads((prior/'cases/exact_deadline/native_boundary.json').read_text())
    assert 499<=native['agent_seconds']<515
    case=json.loads((prior/'cases/exact_deadline/result.json').read_text())
    assert case['child_HTTP_cancelled'] and case['HTTP']['passed'] and case['HTTP']['partial_token_usage']
    assert case['HTTP']['rows'][-1]['usage'] is None
    assert json.loads((prior/'cases/exact_deadline/post_deadline_stability.json').read_text())['unchanged']
    assert json.loads((prior/'cases/exact_deadline/cleanup.json').read_text())['complete']
    sixty=json.loads((prior/'cases/exact_budget/result.json').read_text());assert sixty['counted_tools']==60
    closed=json.loads((prior/'cases/native_closed_loop/result.json').read_text());assert closed['closed_loop'] and closed['explicit_submit']
    current=HERE/'results'/revision
    gate=json.loads((current/'validation/cpu_gate.json').read_text())
    assert gate['passed'] and gate['test_methods']==1 and gate['original115']['passed'] and gate['original115']['tests_run']==115
    assert gate['failures']==gate['errors']==gate['skipped']==0
    assert json.loads((current/'validation/eval_config_public_API.json').read_text())['passed']
    reg=json.loads((HERE/'registrations'/(revision+'.json')).read_text())
    old_reg=json.loads((HERE/'registrations/cpu03.json').read_text())
    prefix='s2/egv_agenttool_t500_v01/'
    selected=('submission.zip','config.py','worker.py','worker_entry.py','runner_observer.py','runtime_audit.py','validation.py',
              'tests/runner_cases.py','tests/test_closed_loop.py','tests/test_exact_budget.py')
    tested={n:h for n,h in reg['source_hashes'].items() if n.startswith((prefix+'candidate/',prefix+'control_single_t500/')) or n in [prefix+s for s in selected]}
    for n,h in tested.items():
        assert sha_file(ROOT/n)==h,n
        assert old_reg['source_hashes'][n]==h,'Core runtime drift between CPU03/04: '+n
    accepted=dict(passed=True,revision=revision,original115_passed=True,original115_test_methods=115,
        acceptance_type='COMPOSITE_DISTINCT_PREPARATIONS',core_preparation='cpu03',core_passed_methods=8,core_preparation_overall_passed=False,
        corrected_configuration_preparation=revision,corrected_configuration_methods=1,actual_deadline_seconds=500,
        observed_native_deadline_seconds=native['agent_seconds'],shared_counted_tools=60,candidate_zip_sha256=sha_file(HERE/'submission.zip'),tested_runtime_hashes=tested,
        core_raw_sha256=sha_file(HERE/'results/cpu03/raw.zip'),final_raw_sha256=sha_file(current/'raw.zip'),
        source_note='CPU03 has one real test error (omitted constructor arguments). Only that configuration test changed for CPU04;8 passing core methods and actual500s native evidence retain immutable CPU03 provenance. CPU04 reran corrected configuration and all115 originals. No fictional9/9 single preparation.',GPU=False,Gemma_inference=False)
    write_new(HERE/'CPU_FEASIBILITY.json',(json.dumps(accepted,indent=2)+'\n').encode())
    print('Composite CPU acceptance:',accepted['observed_native_deadline_seconds'],'seconds; CPU03 eight methods + CPU04 one method and115 original regressions')

if __name__=='__main__':
    import sys
    main(sys.argv[1] if len(sys.argv)>1 else 'cpu04')
