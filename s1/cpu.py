"""Pinned official Linux CPU/API plus new configuration and full Runner gates."""
import importlib.metadata
import json
import os
from pathlib import Path
import sys
import unittest
from harness_v2.cpu_validation import flatten
from harness_v2.evidence import atomic_json
from s1 import VERSION


def main():
    output=Path(sys.argv[1]);output.mkdir(parents=True,exist_ok=False)
    source=Path(__file__).resolve().parents[1]
    os.environ['HARNESS_V2_TEST_EVIDENCE_DIR']=str(output/'workers')
    os.environ['S1_RUNNER_EVIDENCE']=str(output/'runner')
    loader=unittest.TestLoader()
    old=list(flatten(loader.discover(str(source/'tests'),pattern='test_harness_v2*.py')))
    old=[t for t in old if not t.id().endswith('test_baseline_hashes_and_archives_remain_unchanged')]
    old+=list(flatten(loader.discover(str(source/'tests'),pattern='test_official_tools.py')))
    static=list(flatten(loader.discover(str(source/'tests'),pattern='test_submission.py')))
    new=list(flatten(loader.loadTestsFromNames(['s1.tests.test_core','s1.tests.test_runner','s1.tests.test_worker','s1.tests.test_preflight','s1.tests.test_window'])))
    versions={p:importlib.metadata.version(p) for p in ('swegemma','adk-submission','adk-eval-core',
        'google-adk','google-genai','litellm','psutil')}
    with (output/'tests.log').open('x') as log:
        result=unittest.TextTestRunner(stream=log,verbosity=2).run(unittest.TestSuite(old+static+new))
    gate=dict(version=VERSION,passed=result.wasSuccessful() and not result.skipped,
        tests_run=result.testsRun,legacy_count=len(old),static_count=len(static),new_count=len(new),failures=len(result.failures),
        errors=len(result.errors),skipped=len(result.skipped),versions=versions,
        real_official_Runner=True,HTTP_mock=True,Gemma_inference=False,
        source_hashes=json.loads((source/'s1/registration.json').read_text())['source_hashes'])
    atomic_json(output/'cpu_gate.json',gate)
    print(json.dumps(gate,indent=2),flush=True)
    return 0 if gate['passed'] else 1


if __name__=='__main__': sys.exit(main())
