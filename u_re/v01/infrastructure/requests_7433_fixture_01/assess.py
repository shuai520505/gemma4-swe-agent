"""Host-side assessment of preserved raw evidence, never an online evaluator."""
import hashlib
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent


def read(path):return json.loads(Path(path).read_text())


def assess(root):
    root=Path(root)
    native=root/'native_baseline'
    diag=root/'diagnostics'
    env=json.loads(read(diag/'environment.json')['stdout'])
    fixture_records=[json.loads(s) for s in (diag/'fixture_lookup.jsonl').read_text().splitlines()]
    collection=[r for r in fixture_records if r['stage']=='collection']
    assert len(collection)==1
    defs=collection[0]['fixtures']
    cases=list(ET.parse(native/'phase2.junit.xml').getroot().iter('testcase'))
    errors=[(c,c.find('error')) for c in cases if c.find('error') is not None]
    failures=[c for c in cases if c.find('failure') is not None]
    skipped=[c for c in cases if c.find('skipped') is not None]
    recursion={n:sum(("recursive dependency involving fixture '"+n+"'") in (e.text or '') for c,e in errors)
               for n in ('httpbin','httpbin_secure')}
    wheels=read(root/'wheel_inventory.json')
    providers={label:[name for name,row in rows.items() if row['provider_modules']
                     or 'httpbin' in name.lower() or 'trustme' in name.lower()]
               for label,rows in wheels.items()}
    command=read(native/'phase2_command.json')['command']
    original=read(HERE.parents[1]/'results/cpu03/validation/requests_7433/phase2_command.json')['command']
    normalize=lambda s:re.sub(r'/tmp/_swegemma_junit_[a-f0-9]+\.xml','<NATIVE_RANDOM_JUNIT_PATH>',s)
    native_unchanged=normalize(command)==normalize(original)
    comparisons=[read(root/p) for p in ('before_native_files.json','after_native_files.json','after_diagnostics_files.json')]
    files_unchanged=comparisons[0]==comparisons[1]==comparisons[2]
    cleanup=read(root/'cleanup.json')
    import_failure=read(diag/'explicit_provider_import.json')
    offline=read(diag/'offline_provider_resolution.json')
    missing=all(env['versions'][n] is None for n in ('pytest-httpbin','httpbin')) and all(env['modules'][n] is None for n in ('pytest_httpbin','httpbin'))
    absent_ep=not any(e['value']=='pytest_httpbin.plugin' for e in env['pytest11'])
    local_only=all(len(defs[n])==1 and defs[n][0]['file'].endswith('/tests/conftest.py') and n in defs[n][0]['arguments'] for n in ('httpbin','httpbin_secure'))
    root_proven=(missing and absent_ep and local_only and not any(providers.values())
                 and import_failure['exit_code']!=0 and offline['exit_code']!=0
                 and sum(recursion.values())==len(errors) and len(errors)>0)
    outcome='ENVIRONMENT_BLOCKED'
    return dict(outcome=outcome,root_cause_proven_in_research_environment=root_proven,
                cause='Required pytest-httpbin provider distribution/module/entrypoint absent in pinned research environment and both approved wheel caches; only recursive local wrappers registered' if root_proven else 'Evidence incomplete or different; retain environment block and inspect raw records',
                provider=dict(intended_distribution='pytest-httpbin==2.1.0',module='pytest_httpbin.plugin',entrypoint='pytest11:httpbin',
                              module_origin=env['modules']['pytest_httpbin'],fixture_definitions=defs),
                counts=dict(tests=len(cases),passed=len(cases)-len(errors)-len(failures)-len(skipped),
                            assertion_failures=len(failures),setup_errors=len(errors),skipped_junit_entries=len(skipped)),
                recursive_error_counts=recursion,
                native_audit=read(native/'structured_verifier.json'),
                native_test_exit_code=read(native/'official_result.json')['test_exit_code'],
                native_command_equal_except_random_junit_path=native_unchanged,
                observer_in_native_command='_ure_fixture_observer' in command,
                source_test_configuration_unchanged=files_unchanged,files_checked=len(comparisons[0]),
                cleanup_complete=cleanup['complete'] and not cleanup['remaining_directories'],
                native_junit_capture=read(native/'phase2_junit_capture.json'),
                python=env['python'],versions=env['versions'],pytest11=env['pytest11'],
                plugin_load_sequence=collection[0]['plugins'],
                registered_entrypoint_plugins=collection[0]['entrypoint_plugins'],environment=env['environment'],
                approved_wheel_counts={label:len(rows) for label,rows in wheels.items()},provider_wheels=providers,
                offline_resolution_exit=offline['exit_code'],explicit_import_exit=import_failure['exit_code'],
                synthetic_cases=read(root/'minimal/result.json'),
                task_identity=read(root/'task_identity.json'),
                GPU=False,Agent_runs=0,model_calls=0,official_fix_applied=False,
                private_scoring_environment_examined=False,
                protocol_status='DRAFT_BASELINE_BLOCKED',
                limitations=['No approved provider artifact available; no actual provider compatibility/execution test was possible.',
                             'Only normal httpbin lookup is instrumented; secure wrapper absence is independently shown by collection definitions and four native setup traces.',
                             'Synthetic sentinel providers demonstrate pytest resolution semantics only; they are not a research-only Requests environment fix.'])


if __name__=='__main__':
    result=assess(sys.argv[1])
    target=Path(sys.argv[2]) if len(sys.argv)>2 else HERE/'ASSESSMENT.json'
    with target.open('x') as out:json.dump(result,out,indent=2)
    print(json.dumps({k:result[k] for k in ('outcome','root_cause_proven_in_research_environment','counts','approved_wheel_counts','provider_wheels','native_command_equal_except_random_junit_path','source_test_configuration_unchanged','cleanup_complete')},indent=2))
