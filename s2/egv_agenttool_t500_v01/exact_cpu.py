"""Separate exact-limit CPU proof, not model inference or public task scoring."""
import json
import os
from pathlib import Path
import sys
import unittest
from harness_v2.evidence import atomic_json


def main(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    os.environ['S2_CPU_EVIDENCE']=str(output/'cases')
    suite=unittest.defaultTestLoader.loadTestsFromName('s2.egv_agenttool_t500_v01.tests.test_exact_budget')
    with (output/'exact_tests.log').open('x') as log:
        r=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    gate=dict(passed=r.wasSuccessful() and not r.skipped,tests_run=r.testsRun,failures=len(r.failures),errors=len(r.errors),
        skipped=len(r.skipped),actual_native_Agent_seconds=500,actual_counted_tool_cap=60,
        real_Compiler=True,real_ADK_Runner=True,mocked_HTTP=True,Gemma_inference=False,GPU=False)
    atomic_json(output/'exact_gate.json',gate)
    assert gate['passed']
    print(json.dumps(gate,indent=2))


if __name__=='__main__':main(sys.argv[1])
