"""Frozen113 gate + new candidate actual Compiler/Runner path, then CPU attribution."""
import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from harness_v2.evidence import atomic_json


def main(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    result=subprocess.run([sys.executable,'-m','s1.experiments.e3_structured_smoke_04.cpu',str(output/'frozen113')],capture_output=True,text=True,timeout=2600)
    (output/'frozen113.stdout.log').write_text(result.stdout);(output/'frozen113.stderr.log').write_text(result.stderr)
    gate=json.loads((output/'frozen113/cpu_gate.json').read_text())
    assert result.returncode==0 and gate['passed'] and gate['tests_run']==113
    os.environ['EGV_CPU_EVIDENCE']=str(output/'candidate')
    (output/'candidate').mkdir()
    suite=unittest.defaultTestLoader.loadTestsFromName('s1.egv_v01.tests.CandidateTests')
    with (output/'candidate_tests.log').open('x') as log:tests=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    candidate_gate=dict(passed=tests.wasSuccessful() and not tests.skipped,actual_tests=tests.testsRun,failures=len(tests.failures),errors=len(tests.errors),skipped=len(tests.skipped),real_Compiler_Runner=True,mocked_HTTP=True,Gemma_inference=False)
    atomic_json(output/'candidate_gate.json',candidate_gate)
    assert candidate_gate['passed'] and tests.testsRun==2
    # Separate evaluator-only process; no historical score mutation or model.
    diagnostic=subprocess.run([sys.executable,'-m','s1.egv_v01.rich_diagnostics',str(output/'rich_attribution')],capture_output=True,text=True,timeout=900)
    (output/'diagnostics.stdout.log').write_text(diagnostic.stdout);(output/'diagnostics.stderr.log').write_text(diagnostic.stderr)
    atomic_json(output/'cpu_gate.json',dict(passed=diagnostic.returncode==0,frozen_gate=gate,new_candidate_gate=candidate_gate,CPU_tests=113+tests.testsRun,GPU=False,real_inference=False,diagnostics_exit_code=diagnostic.returncode))
    assert diagnostic.returncode==0,'Read-only attribution incomplete; inspect preserved logs'


if __name__=='__main__':main(sys.argv[1])
