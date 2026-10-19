"""CPU controller/API regressions and a separately reported task eligibility gate."""
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

from harness_v2.evidence import atomic_json
from .workspace_check import check


def main(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    source=Path(__file__).resolve().parents[2]
    # The 77 old tests run in another process to preserve disposable-worker
    # logging isolation before the real native Agent deadline test.
    native=subprocess.run([sys.executable,'-m','s1.experiments.e1_outputcap_smoke_02.cpu',str(output/'baseline77')],
        cwd=source,capture_output=True,text=True,timeout=1500)
    (output/'baseline77.stdout.log').write_text(native.stdout)
    (output/'baseline77.stderr.log').write_text(native.stderr)
    baseline=json.loads((output/'baseline77/cpu_gate.json').read_text())
    os.environ['S1_RECOVERY_EVIDENCE']=str(output/'recovery_events')
    tests=unittest.defaultTestLoader.loadTestsFromNames([
        's1.infrastructure_recovery.tests.test_wire','s1.infrastructure_recovery.tests.test_imports',
        's1.infrastructure_recovery.tests.test_gate','s1.infrastructure_recovery.tests.test_official_deadline'])
    tests.addTests(unittest.defaultTestLoader.loadTestsFromName('s1.infrastructure_recovery.tests.test_build_dependencies'))
    with (output/'tests.log').open('x') as log:
        result=unittest.TextTestRunner(stream=log,verbosity=2).run(tests)
    environment=check(output/'clean_requests')
    from .public_preflight import check as public_check
    public=public_check(output/'new_tasks')
    passed=native.returncode==0 and baseline['passed'] and result.wasSuccessful() and not result.skipped
    gate=dict(passed=passed,controller_tests_passed=passed,
        tests_run=baseline['tests_run']+result.testsRun,baseline_tests=baseline['tests_run'],new_tests=result.testsRun,
        failures=baseline['failures']+len(result.failures),errors=baseline['errors']+len(result.errors),
        skipped=baseline['skipped']+len(result.skipped),versions=baseline['versions'],
        source_hashes=json.loads((source/'s1/registration.json').read_text())['source_hashes'],
        requests_verifier_eligible=environment['requests_verifier_eligible'],
        new_task_environment_gates=public,
        overall_requests_GPU_ready=passed and environment['requests_verifier_eligible'],
        real_official_Runner=True,Gemma_inference=False,GPU=False,
        scope='Controller regression success does not mean the Requests fixture gate passed')
    atomic_json(output/'cpu_gate.json',gate)
    print(json.dumps({k:v for k,v in gate.items() if k!='source_hashes'},indent=2),flush=True)
    return 0 if passed else 1


if __name__=='__main__':sys.exit(main(sys.argv[1]))
