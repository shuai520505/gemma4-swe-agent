"""Read-only integrity and native-result checks on this completed smoke."""
import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET
from harness_v2.evidence import read_events
from s1.collect import verify_zip

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]


def inspect():
    def load(p):return json.loads(p.read_text())
    out=HERE/'results/gpu01';run=out/'runs/01-rich_3471-B'
    plan=load(HERE/'protocol_cpu02.json')
    cpu=verify_zip((HERE/'results/cpu02/raw.zip').read_bytes())
    gpu=verify_zip((out/'raw.zip').read_bytes())
    raw=load(run/'official_result.json');audit=load(run/'research_audit.json')
    assert raw['resolved'] is True and raw['test_exit_code']==0
    assert audit['infrastructure_passed'] and not audit['reasons']
    assert load(out/'batch_gate.json')['not_run']==[]
    assert load(out/'model_identity.json')['files']==plan['model_files']
    assert load(out/'gpu_host_environment/rich_3471/task_inputs.json')==plan['task_inputs']
    candidate=ROOT/'s2/egv_agenttool_t500_v01/submission.zip'
    assert hashlib.sha256(candidate.read_bytes()).hexdigest()==plan['candidates']['B']['zip_sha256']
    for name,h in plan['candidates']['B']['members'].items():
        assert hashlib.sha256((candidate.parent/'candidate'/name).read_bytes()).hexdigest()==h
    counts=audit['structured_verifier']['counts']
    assert counts==dict(tests=108,failures=0,errors=0,skipped=0)
    xml=(run/'phase2.junit.xml').read_bytes();capture=load(run/'phase2_junit_capture.json')
    assert hashlib.sha256(xml).hexdigest()==capture['sha256'] and capture['sandbox_exists_at_capture']
    cases=ET.fromstring(xml).findall('.//testcase')
    assert len(cases)==108 and not any(c.find('failure') is not None or c.find('error') is not None for c in cases)
    assert load(run/'phase2_command.json')['native_command_unchanged']
    nested=load(run/'nested_metrics.json')
    assert nested['delegations']==[] and nested['model_start_events_by_role']=={'main_coding_agent':50}
    assert not nested['child_workspace_side_effects']
    wire=[r for r in read_events(run/'http_wire.jsonl') if r['kind']=='http_request']
    assert len(wire)==56
    main=[r for r in wire if r['body'].get('tools')]
    assert len(main)==50
    assert all('egv_verifier' in {t['function']['name'] for t in r['body']['tools']} for r in main)
    assert all(r['body']['model'].endswith('/gemma-4-31b-it-qat-w4a16-ct/2') and
        r['body']['seed']==17 and r['body'].get('max_completion_tokens',r['body'].get('max_tokens'))==16384
        and r['body']['thinking_token_budget']==4096 for r in wire)
    terminal=audit['http_lifecycle']
    assert terminal['passed'] and len(terminal['rows'])==56
    cancelled=[r for r in terminal['rows'] if r['terminal_status']=='cancelled']
    assert len(cancelled)==1 and cancelled[0]['explained_cancellation'] and cancelled[0]['usage'] is None
    assert audit['deadline_proof']['official_agent_deadline'] and audit['partial_token_usage']
    assert audit['server_idle']['consecutive_idle_snapshots']==3
    assert load(out/'server_cleanup.json')['verified'] and load(run/'worker_done.json')['cleanup_complete']
    # Corrected source is independently executed in the native verifier workspace.
    modified_sha=capture['production_source_hashes']['rich/text.py']
    provenance=[]
    for p in (run/'import_audit').rglob('*-exit.json'):
        d=load(p);module=d.get('modules',{}).get('rich.text',{})
        if '/swegemma_sandbox_0f09a67b-dc5/' in d.get('cwd','') and module.get('source_sha256')==modified_sha:
            assert module['realpath'].startswith(capture['workspace_realpath']+'/')
            provenance.append(p.relative_to(out).as_posix())
    assert provenance
    # No historical candidate, evidence or protocol edited on this branch.
    changed=subprocess.check_output(['git','-c','core.longpaths=true','diff','--name-only',
        '25f6fed8b681398b23ffec9c8a162b63f203fa00'],cwd=ROOT,text=True).splitlines()
    assert all(p.startswith('s2/experiments/t500_agenttool_smoke_01/') for p in changed),changed
    return dict(passed=True,cpu_archive=cpu,gpu_archive=gpu,original_Phase2_counts=counts,
        official_resolved=raw['resolved'],EGV_called=False,autonomous_dual_agent_loop=False,
        explicit_submit=False,native_fallback_patch=True,HTTP_requests=56,HTTP_responses=55,
        cancelled_request=cancelled[0],partial_usage=True,provenance_pointers=provenance,
        historical_tracked_changes=[],scope='Read-only evidence verification; not a second model run or a repair-rate comparison.')


if __name__=='__main__':print(json.dumps(inspect(),indent=2))
