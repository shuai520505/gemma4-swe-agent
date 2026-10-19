"""Replay all 71 r04 gates, then exercise the additional passive startup observer."""
import json
from pathlib import Path
import sys
import unittest
from harness_v2.evidence import atomic_json


def main():
    from s1.cpu import main as r04_cpu
    output=Path(sys.argv[1])
    status=r04_cpu()
    original=json.loads((output/'cpu_gate.json').read_text())
    atomic_json(output/'r04_gate.json',original)
    suite=unittest.defaultTestLoader.loadTestsFromName(
        's1.experiments.e1_outputcap_smoke_02.test_startup')
    with (output/'startup_tests.log').open('x') as log:
        result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    gate=dict(original)
    gate.update(passed=status==0 and result.wasSuccessful() and not result.skipped,
        tests_run=original['tests_run']+result.testsRun,
        startup_observer_count=result.testsRun,
        failures=original['failures']+len(result.failures),
        errors=original['errors']+len(result.errors),skipped=original['skipped']+len(result.skipped),
        Gemma_inference=False)
    atomic_json(output/'cpu_gate.json',gate)
    print(json.dumps(gate,indent=2),flush=True)
    return 0 if gate['passed'] else 1


if __name__=='__main__':sys.exit(main())
