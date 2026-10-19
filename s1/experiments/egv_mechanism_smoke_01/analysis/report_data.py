"""Read-only post-run audit; never packaged into a candidate or GPU payload."""
import csv
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from s1.verifier_v3.audit import audit_verifier

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
GPU = STUDY / 'results/gpu'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def lines(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    raw = (json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode()
    if path.exists():
        assert path.read_bytes() == raw, f'Derived audit changed: {path}'
    else:
        path.write_bytes(raw)


def main():
    sealed = HERE / 'FIRST_PASS_SEALED.json'
    assert digest(sealed) == (HERE / 'FIRST_PASS_SEALED.sha256').read_text().split()[0]
    mapping = read(STUDY / '_local/blind_mapping.json')
    save(HERE / 'UNBLINDED_MAPPING.json', mapping)
    protocol = read(STUDY / 'protocol.json')
    baseline = read(GPU / 'gpu_host_environment/environment_admission.json')
    assert baseline['eligible']
    summary = {}
    replay = {}
    provenance = []
    timeline = []
    for label, identity in mapping.items():
        directory = GPU / 'runs' / identity['run']
        arm = identity['run'].rsplit('-', 1)[1]
        assert digest(directory / 'adk_events.jsonl') == identity['ADK_sha256']
        actions = read(HERE / 'masked' / (label + '.json'))['actions']
        audit = read(directory / 'research_audit.json')
        official = read(directory / 'official_result.json')
        assert official['agent_patch'].encode() == (directory / 'latest.patch').read_bytes()
        events = lines(directory / 'events.jsonl')
        origin = next(e['recorded_monotonic'] for e in events if e.get('agent_started'))
        native = audit_verifier(directory, baseline=baseline)
        assert native == audit['structured_verifier'], arm
        replay[arm] = native
        requests = [e for e in lines(directory / 'http_wire.jsonl') if e['kind'] == 'http_request']
        for request in requests:
            body = request['body']
            assert body['model'].endswith('gemma-4-31b-it-qat-w4a16-ct/2')
            assert body['max_completion_tokens'] == 16384 and body['seed'] == 17
            assert body['thinking_token_budget'] == 4096
            assert body['chat_template_kwargs'] == {'enable_thinking': True}
            assert not any(k in body for k in ('temperature', 'top_p', 'top_k', 'include_thoughts'))
            if body.get('tools'):
                assert tuple(t['function']['name'] for t in body['tools']) == (
                    'get_status', 'run_command', 'read_file', 'edit_file', 'write_file', 'submit_patch')
        wire_system = requests[0]['body']['messages'][0]['content']
        prompt_path = 's1/egv_v01/candidate/prompts/system.md' if arm == 'egv' else 's1/candidates/control/prompts/system.md'
        prompt = (STUDY.parents[2] / prompt_path).read_text(encoding='utf-8')
        assert prompt.strip() in wire_system
        context = [e for e in events if e['kind'] == 'context_admission']
        assert all(e.get('decision') == 'allow' and e['total_reserved'] <= 32768 for e in context)
        production_edits = []
        for action in actions:
            row = dict(action, arm=arm, masked_case=label,
                       agent_seconds=round(action['call_time'] - origin, 6),
                       response_agent_seconds=round(action['response_time'] - origin, 6))
            timeline.append(row)
            if action['tool'] in ('edit_file', 'write_file') and action['args'].get('filepath', '').startswith('fastapi/'):
                assert action['response']['status'] == 'ok'
                production_edits.append(dict(index=action['index'], seconds=row['agent_seconds'],
                    returned_seconds=row['response_agent_seconds'], filepath=action['args']['filepath']))
            command = action['args'].get('command', '')
            if action['tool'] == 'run_command' and ('pytest ' in command or command.startswith('python3')):
                for f in directory.glob('import_audit/*/*-startup.json'):
                    start = read(f)
                    if action['call_time'] <= start['recorded_monotonic'] <= action['response_time']:
                        exit_path = f.with_name(f.name.replace('-startup.json', '-exit.json'))
                        ending = read(exit_path) if exit_path.exists() else {}
                        modules = ending.get('modules', {})
                        provenance.append(dict(arm=arm, action=action['index'], command=command,
                            startup=f.relative_to(STUDY).as_posix(), sys_path=start['sys_path'],
                            exit=exit_path.relative_to(STUDY).as_posix(),
                            modules={k:v for k,v in modules.items() if k in ('fastapi', 'fastapi.applications', 'fastapi.routing')},
                            scope='Module execution/import evidence. Target reach additionally requires tool test arguments and results.'))
        xml = ET.parse(directory / 'phase2.junit.xml')
        failures = [dict(name=e.get('name'), message=c.get('message'))
                    for e in xml.iter('testcase') for c in e if c.tag in ('failure', 'error')]
        h = audit['http_lifecycle']
        assert h['passed'] and h['requests'] == len(requests)
        assert all(r['terminal_status'] in ('response_received', 'cancelled') for r in h['rows'])
        assert all(r['usage'] is None and r['explained_cancellation'] for r in h['rows'] if r['terminal_status'] == 'cancelled')
        assert audit['infrastructure_passed']
        assert read(directory / 'audit_result.json')['cleanup_complete']
        assert read(directory / 'server_reclamation/idle_gate.json')['passed']
        summary[arm] = dict(official_resolved=official['resolved'], test_exit_code=official['test_exit_code'],
            phase2=native['counts'], phase2_summary=native['summary'], phase2_category=native['category'],
            attribution=native['attribution'], official_LLM_calls=official['total_llm_calls'],
            tool_calls=official['tool_calls'], HTTP_requests=h['requests'], responses=h['responses'],
            summary_requests=[i+1 for i,r in enumerate(requests) if not r['body'].get('tools')],
            usage=h['observed_response_usage'], usage_complete=h['usage_complete'],
            cancellation=h['rows'][-1], deadline=audit['deadline_proof'],
            agent_seconds=audit['agent_seconds'], worker_seconds=audit['worker_seconds'],
            phase2_seconds=audit['phase2']['duration_seconds'], production_edits=production_edits,
            first_production_diff_seconds=production_edits[0]['returned_seconds'],
            whole_task_stable_repair_seconds=None, exact_repeated_reads=audit['exact_repeated_reads'],
            maximum_admitted_input=max(e['input_tokens'] for e in context),
            explicit_submit=False, patch_bytes=audit['patch_bytes'], patch_sha256=digest(directory / 'latest.patch'),
            patch_files=re.findall(r'^diff --git a/(.*?) b/', official['agent_patch'], re.M),
            JUnit_sha256=digest(directory / 'phase2.junit.xml'), failures=failures)
    for name, expected in [('wheel_hashes.json', protocol['wheel_hashes']),
                           ('task_wheel_hashes.json', protocol['task_wheel_hashes'])]:
        assert read(GPU / name) == expected, name
    assert read(GPU / 'model_identity.json')['files'] == protocol['model_files']
    assert read(GPU / 'server_cleanup.json')['verified']
    assert read(GPU / 'batch_gate.json')['infrastructure_passed']
    save(HERE / 'NATIVE_VERIFIER_REPLAY.json', replay)
    save(HERE / 'TOOL_TIMELINE.json', timeline)
    save(HERE / 'PROBE_PROVENANCE.json', provenance)
    save(HERE / 'METRICS.json', summary)
    platform = read(GPU / 'gemma4-s1-egv-mech01-gpu.log')
    seconds = max(row['time'] for row in platform)
    save(HERE / 'COST_SCOPE.json', dict(platform_last_event_seconds=seconds,
        GPU_device_seconds_proxy=4*seconds, GPU_device_hours_proxy=4*seconds/3600,
        four_L4_admission='Frozen coordinator asserted torch count4 and all device names contain L4 before server startup; no separate device inventory file was saved.',
        startup_generation_seconds=read(GPU/'gpu_probe.json')['startup_seconds'],
        startup_token_usage=read(GPU/'gpu_probe.json')['response']['usage'],
        scope='Platform runtime proxy including installs/model startup/two arms/cleanup/export; excludes queue. Not billing or isolated inference time. Missing cancelled usage is not imputed.'))
    print('Read-only native replay, request parameters, SHA, cleanup and source-path joins passed.')


if __name__ == '__main__':
    main()
