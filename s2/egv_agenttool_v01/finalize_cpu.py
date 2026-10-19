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
    assert gate['test_methods']==4 and gate['failures']==gate['errors']==gate['skipped']==0
    reg=json.loads((HERE/'registrations'/(revision+'.json')).read_text())
    tested={n:h for n,h in reg['source_hashes'].items() if n.startswith('s2/egv_agenttool_v01/candidate/') or n in
        ['s2/egv_agenttool_v01/'+name for name in ('submission.zip','worker.py','worker_entry.py','runner_observer.py','runtime_audit.py','validation.py')]}
    for n,h in tested.items():assert sha_file(ROOT/n)==h,n
    candidate=json.loads((HERE/'candidate.json').read_text())
    accepted=dict(passed=True,revision=revision,original115_passed=True,
        original115_test_methods=115,new_ADK_test_methods=4,named_ADK_scenarios=23,
        candidate_zip_sha256=candidate['zip_sha256'],tested_runtime_hashes=tested,
        raw_archive_sha256=sha_file(result/'raw.zip'),gate_sha256=sha_file(result/'validation/cpu_gate.json'),
        GPU=False,Gemma_inference=False,scope='CPU model responses are scripted; official tools, source edits, assertions, feedback delivery, native budgets/deadline and submission are real. Additional environment/integration gates are separate.')
    write_new(HERE/'CPU_FEASIBILITY.json',(json.dumps(accepted,indent=2)+'\n').encode())
    print('CPU acceptance derived from',revision,'candidate',candidate['zip_sha256'])


if __name__=='__main__':
    import sys
    main(sys.argv[1])
