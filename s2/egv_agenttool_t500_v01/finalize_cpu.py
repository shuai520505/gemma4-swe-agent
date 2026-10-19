"""Derive acceptance only from a complete, archived actual CPU preparation."""
import hashlib
import json
from pathlib import Path
from experiments.prepare import write_new
from s1.util import sha_file

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def main(revision):
    result=HERE/'results'/revision
    gate=json.loads((result/'validation/cpu_gate.json').read_text())
    assert gate['passed'] and gate['original115']['passed'] and gate['original115']['tests_run']==115
    assert gate['test_methods'] ==9 and gate['failures']==gate['errors']==gate['skipped']==0
    reg=json.loads((HERE/'registrations'/(revision+'.json')).read_text())
    tested={n:h for n,h in reg['source_hashes'].items() if n.startswith(('s2/egv_agenttool_t500_v01/candidate/','s2/egv_agenttool_t500_v01/control_single_t500/')) or n in
        ['s2/egv_agenttool_t500_v01/'+name for name in ('submission.zip','config.py','worker.py','worker_entry.py','runner_observer.py','runtime_audit.py','validation.py')]}
    for n,h in tested.items():assert sha_file(ROOT/n)==h,n
    candidate=json.loads((HERE/'candidate.json').read_text())
    accepted=dict(passed=True,revision=revision,original115_passed=True,
        original115_test_methods=115,new_ADK_test_methods=4,named_ADK_scenarios=23,
        statistics_test_methods=2,exact_budget_test_methods=2,eval_config_test_methods=1,actual_deadline_seconds=500,
        candidate_zip_sha256=candidate['zip_sha256'],tested_runtime_hashes=tested,
        raw_archive_sha256=sha_file(result/'raw.zip'),gate_sha256=sha_file(result/'validation/cpu_gate.json'),
        GPU=False,Gemma_inference=False,scope='CPU model responses are scripted; official tools, source edits, assertions, feedback delivery, native budgets/deadline and submission are real. Additional environment/integration gates are separate.')
    target=HERE/'CPU_FEASIBILITY.json'
    raw=(json.dumps(accepted,indent=2)+'\n').encode()
    if target.exists() and target.read_bytes()!=raw:
        prior=json.loads(target.read_text());write_new(HERE/('CPU_FEASIBILITY_'+prior['revision']+'.json'),target.read_bytes())
        target.write_bytes(raw)
    else:write_new(target,raw)
    print('CPU acceptance derived from',revision,'candidate',candidate['zip_sha256'])


if __name__=='__main__':
    import sys
    main(sys.argv[1])
