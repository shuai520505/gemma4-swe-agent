"""Read-only final acceptance; no model, no writes, no invented GPU outcome."""
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile
from harness_v2.evidence import read_events
from s1.collect import verify_zip

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def inspect():
    def load(p):return json.loads(p.read_text())
    candidate=load(HERE/'candidate.json');old=HERE.parent/'egv_agenttool_t500_v01'
    changed=[]
    with zipfile.ZipFile(HERE/'submission.zip') as z:
        assert z.testzip() is None and set(z.namelist())==set(candidate['members'])
        for name,h in candidate['members'].items():
            raw=z.read(name);assert hashlib.sha256(raw).hexdigest()==h
            assert raw==(HERE/'candidate'/name).read_bytes()
            if raw!=(old/'candidate'/name).read_bytes():changed.append(name)
    assert changed==['prompts/main.md']
    assert hashlib.sha256((old/'submission.zip').read_bytes()).hexdigest()==candidate['parent_zip_sha256']
    acceptance=load(HERE/'CPU_ACCEPTANCE.json');assert acceptance['passed']
    revision=acceptance['revision'];result=HERE/'results'/revision/'validation'
    gate=load(result/'cpu_gate.json');assert gate['passed'] and gate['original115_passed']
    assert gate['new_workflow']['tests_run']==8 and gate['new_workflow']['passed']
    assert gate['new_exact_budget']['tests_run']==2 and gate['new_exact_budget']['passed']
    reg=load(HERE/'registrations'/f'{revision}.json')
    for p in ('cpu.py','runner_cases.py','tests/test_early.py'):
        key='s2/egv_agenttool_t500_early_v01/'+p
        assert hashlib.sha256((HERE/p).read_bytes()).hexdigest()==reg['source_hashes'][key]
    original=verify_zip((HERE/'results'/revision/'raw.zip').read_bytes())
    env=verify_zip((HERE/'results/env01/raw.zip').read_bytes())
    assert load(HERE/'results/env01/validation/environment_gate.json')['passed']
    exact=result/'early_exact_cases/exact_deadline'
    native=load(exact/'native_boundary.json')
    assert 499<=native['agent_seconds']<515
    cancel=load(exact/'result.json');assert cancel['child_HTTP_cancelled'] and cancel['HTTP']['passed']
    assert cancel['HTTP']['rows'][-1]['usage'] is None
    assert load(exact/'post_deadline_stability.json')['unchanged']
    tools=load(result/'early_exact_cases/exact_budget/result.json')
    assert tools['counted_tools']==60 and tools['explicit_submit'] and tools['actual_tool_events']>60
    a=result/'early_cases/A_pre_patch';rows=read_events(a/'nested_audit.jsonl')
    delegation=next((i,r) for i,r in enumerate(rows,1) if r['kind']=='tool_start' and r['tool']=='egv_verifier')
    assert not any(r['kind']=='tool_start' and r['tool'] in ('edit_file','write_file') for r in rows)
    assert delegation[1]['files']['app.py']==hashlib.sha256(b'def accepts(n):\n    return False\n').hexdigest()
    loops={}
    for name in ('B_early_repair','C_post_patch'):
        r=load(result/'early_cases'/name/'result.json')
        assert r['closed_loop'] and r['explicit_submit'] and r['HTTP']['passed']
        loops[name]={k:r[k] for k in ('target_counterevidence','feedback_delivered','feedback_handled','counterevidence_cleared','counted_tools','actual_tool_events','model_requests','actors')}
    draft=load(HERE/'GPU_MECHANISM_PROTOCOL_DRAFT.json')
    assert not draft['GPU_authorized'] and not draft['GPU_executed']
    assert [r['arm'] for r in draft['runs']]==['A','B','B','A']
    assert {r['instance_id'] for r in draft['runs']}=={'rich_3676','fastapi_14492'}
    nb=load(HERE/'notebooks/gpu-draft/study.ipynb')
    assert nb['cells'][0]['source'].startswith('raise RuntimeError(')
    changed_git=subprocess.check_output(['git','-c','core.longpaths=true','diff','--name-only',
        '59eda9c0c100e77fdd6aacee90feb4823f2cfe4b'],cwd=ROOT,text=True).splitlines()
    assert all(n.startswith('s2/egv_agenttool_t500_early_v01/') for n in changed_git),changed_git
    return dict(passed=True,candidate_zip_sha256=candidate['zip_sha256'],changed_candidate_members=changed,
        accepted_CPU_revision=revision,CPU_raw=original,environment_raw=env,
        actual_native_Agent_seconds=native['agent_seconds'],counted_tool_limit=60,
        early_delegation_start_pointer=f'early_cases/A_pre_patch/nested_audit.jsonl:{delegation[0]}',
        closed_loops=loops,historical_changes=[],GPU_started=False,new_formal_submission=False,
        interpretation='Real official CPU paths with scripted model replies; not real-Gemma timing compliance or algorithm gains.')


if __name__=='__main__':print(json.dumps(inspect(),indent=2))
