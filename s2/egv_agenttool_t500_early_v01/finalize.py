"""Accept only actual complete CPU02 evidence; no cross-preparation pass splicing."""
import hashlib
import json
from pathlib import Path
from s1.collect import verify_zip
from experiments.prepare import write_new

HERE=Path(__file__).resolve().parent


def emit(path,d):write_new(path,(json.dumps(d,indent=2)+'\n').encode())


def main():
    def load(p):return json.loads(p.read_text())
    result=HERE/'results/cpu02/validation'
    gate=load(result/'cpu_gate.json')
    assert gate['passed'] and gate['original115_passed']
    counts=[gate['original115']['tests_run'],gate['frozen_T500']['tests_run'],gate['new_workflow']['tests_run'],
        gate['draft_admission_guards']['tests_run'],gate['new_exact_budget']['tests_run']]
    assert counts==[115,7,8,3,2]
    exact=result/'early_exact_cases/exact_deadline'
    native=load(exact/'native_boundary.json');r=load(exact/'result.json')
    assert 499<=native['agent_seconds']<515 and r['child_HTTP_cancelled'] and r['HTTP']['passed']
    assert r['HTTP']['rows'][-1]['usage'] is None
    assert load(exact/'post_deadline_stability.json')['unchanged'] and load(exact/'cleanup.json')['complete']
    budget=load(result/'early_exact_cases/exact_budget/result.json')
    assert budget['counted_tools']==60 and budget['explicit_submit'] and budget['actual_tool_events']>60
    candidate=load(HERE/'candidate.json')
    assert hashlib.sha256((HERE/'submission.zip').read_bytes()).hexdigest()==candidate['zip_sha256']
    reg=load(HERE/'registrations/cpu02.json')
    runtime={}
    for n,h in reg['source_hashes'].items():
        if n.startswith('s2/egv_agenttool_t500_early_v01/') and (n.endswith(('cpu.py','runner_cases.py','tests/test_early.py')) or '/candidate/' in n or n.endswith('/submission.zip')):
            local=HERE/Path(n).relative_to('s2/egv_agenttool_t500_early_v01')
            assert hashlib.sha256(local.read_bytes()).hexdigest()==h,n
            runtime[n]=h
    proof=verify_zip((HERE/'results/cpu02/raw.zip').read_bytes())
    cpu01=load(HERE/'results/cpu01/validation/cpu_gate.json');assert not cpu01['passed']
    emit(HERE/'CPU_ACCEPTANCE.json',dict(passed=True,revision='cpu02',acceptance_type='SINGLE_COMPLETE_PREPARATION',
        tests_run=sum(counts),original115=115,frozen_T500=7,new_workflow=8,guards=3,exact_budget=2,
        source_hashes=runtime,candidate_zip_sha256=candidate['zip_sha256'],raw_sha256=proof['sha256'],
        native_deadline_seconds=native['agent_seconds'],shared_counted_tools=60,
        GPU=False,Gemma_inference=False,prior_failed_preparation_preserved='cpu01'))
    rows={}
    for name in ('A_pre_patch','B_early_repair','C_post_patch','D_close','E_cleanup','H_direct'):
        data=load(result/'early_cases'/name/'result.json')
        rows[name]={k:v for k,v in data.items() if k not in ('all_model_rows','child_side_effects')}
    emit(HERE/'CPU_OBSERVATIONS.json',dict(cases=rows,wrong_expectations=load(result/'early_cases/F_attribution.json'),
        exact_native_seconds=native['agent_seconds'],exact_60=dict(counted=budget['counted_tools'],
            actual_tool_events=budget['actual_tool_events'],explicit_submit=budget['explicit_submit']),
        prompt_tokenization=load(result/'prompt_tokenization.json'),
        scope='Scripted HTTP with actual official tools/edits/assertions/Patch; never Gemma autonomous behavior or latency.'))
    print('CPU_ACCEPTANCE:135/135 in one complete CPU02; prior CPU01 error preserved')


if __name__=='__main__':main()
