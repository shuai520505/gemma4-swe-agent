"""Run genuine pinned verifier guard/JUnit functions only; no repair evaluation."""
import asyncio,hashlib,importlib.metadata,inspect,json,platform,shutil,subprocess,time
from datetime import datetime,timezone
from pathlib import Path
from types import SimpleNamespace

OUT=Path(__file__).resolve().parent/'holdout-preparation'

def main():
    from swegemma.harness.verification import _validate_junit_xml,verify_task
    from swegemma.models import Task
    source=Path(inspect.getsourcefile(verify_task))
    sha=lambda b:hashlib.sha256(b).hexdigest()
    suite=lambda body,tests=1,failures=0,errors=0,skipped=0:f'<testsuite tests="{tests}" failures="{failures}" errors="{errors}" skipped="{skipped}">{body}</testsuite>'
    cases=[
        ('required_pass',suite('<testcase classname="tests.test_contract" name="test_target"/>'),('tests/test_contract.py::test_target',),True),
        ('missing_required_node',suite('<testcase name="test_other"/>'),('test_target',),False),
        ('required_skip',suite('<testcase name="test_target"><skipped/></testcase>',skipped=1),('test_target',),False),
        ('failed_test',suite('<testcase name="test_target"><failure/></testcase>',failures=1),('test_target',),False),
        ('collection_error',suite('<testcase name="test_target"><error/></testcase>',errors=1),('test_target',),False),
        ('zero_tests',suite('',tests=0),(),False),
        ('missing_xml','',(),False),
        ('malformed_xml','<testsuite',(),False),
    ]
    results=[]
    for name,xml,required,expected in cases:
        valid,reason=_validate_junit_xml(xml,fail_to_pass=required)
        results.append(dict(case=name,expected=expected,actual=valid,reason=reason,passed=valid==expected))
    assert all(r['passed'] for r in results)
    # Only a fabricated identity, no real Issue/test/reference patch. This branch MUST reject before sandbox start.
    task=Task(instance_id='cpu-contract-no-tests',repo='owned/contract',base_commit='0'*40,problem_statement='CPU guard contract only')
    guard=asyncio.run(verify_task(None,SimpleNamespace(results_dir=None),task,Path('NEVER_OPENED'),start_time=time.perf_counter()))
    assert guard.resolved is False and guard.test_exit_code==-1 and 'Missing test specification' in guard.error
    wsl=shutil.which('wsl');docker=shutil.which('docker')
    wsl_result=None
    if wsl:
        p=subprocess.run([wsl,'--list','--quiet'],capture_output=True,timeout=15)
        wsl_result={'exit_code':p.returncode,'stdout_bytes':len(p.stdout),'stderr_bytes':len(p.stderr),'stdout_sha256':sha(p.stdout),'stderr_sha256':sha(p.stderr)}
    summary={
        'status':'CPU_CONTRACT_PASS_NATIVE_ENDPOINT_NOT_RUN',
        'checked_at_utc':datetime.now(timezone.utc).isoformat(),
        'evidence':'CPU_VERIFIED_OFFICIAL_FUNCTION_CONTRACT_ONLY',
        'version':importlib.metadata.version('swegemma'),
        'official_verification_file':str(source),'official_verification_sha256':sha(source.read_bytes()),
        'junit_cases':results,
        'missing_spec_guard':{'resolved':guard.resolved,'exit_code':guard.test_exit_code,'error':guard.error,'sandbox_started':False},
        'host':platform.system(),'docker_executable':docker,'wsl_query':wsl_result,
        'linux_sandbox_available':False if platform.system()=='Windows' and docker is None and wsl_result and wsl_result['exit_code']!=0 else None,
        'complete_verify_task_lifecycle':'NOT_RUN',
        'prospective_bug_reproduction':'NOT_RUN_NO_ELIGIBLE_TASK',
        'prospective_positive_control':'NOT_RUN_NO_ELIGIBLE_TASK',
        'native_resolved':None,'repair_capability_evidence':False,
        'reference_repair_used':False,'model_requests':0,'GPU_notebooks':0,
        'limitations':'Generated XML checks and fail-closed guard are not a native task test, snapshot/dependency validation, positive control, sandbox proof or model repair evidence.'
    }
    OUT.mkdir(exist_ok=True)
    (OUT/'NATIVE_CPU_CONTRACT_RESULT.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'status':summary['status'],'junit_cases_passed':len(results),'missing_spec_guard':'PASS','native_endpoint':'NOT_RUN','linux_sandbox_available':summary['linux_sandbox_available']}))

if __name__=='__main__':main()
