"""CPU gate for the real organizer API and controller, with no model generation."""
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import sys
import unittest

from .evidence import atomic_json
from . import VERSION


def flatten(suite):
    for item in suite:
        if isinstance(item,unittest.TestSuite): yield from flatten(item)
        else: yield item


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('output',type=Path)
    args=p.parse_args()
    root=Path(__file__).resolve().parents[1]
    args.output.mkdir(parents=True,exist_ok=True)
    os.environ['HARNESS_V2_TEST_EVIDENCE_DIR']=str(args.output/'workers')
    loader=unittest.TestLoader()
    tests=list(flatten(loader.discover(str(root/'tests'),pattern='test_harness_v2*.py')))
    # The private baseline is checked on its source machine before this upload.
    # Neither old traces nor task patches are mounted into the infrastructure bundle.
    excluded=[t.id() for t in tests if t.id().endswith('test_baseline_hashes_and_archives_remain_unchanged')]
    tests=[t for t in tests if t.id() not in excluded]
    tests+=list(flatten(loader.discover(str(root/'tests'),pattern='test_official_tools.py')))
    atomic_json(args.output/'test_selection.json',dict(selected=[t.id() for t in tests],
        excluded=excluded,excluded_reason='Private baseline already hash-verified locally; never included in Agent input'))
    versions={p:importlib.metadata.version(p) for p in ('swegemma','adk-submission','adk-eval-core',
        'google-adk','google-genai','litellm','psutil')}
    atomic_json(args.output/'versions.json',versions)
    with (args.output/'cpu_tests.log').open('x',encoding='utf-8') as log:
        result=unittest.TextTestRunner(stream=log,verbosity=2).run(unittest.TestSuite(tests))
    gate=dict(schema_version=2,harness_version=VERSION,kind='cpu_only_no_model_inference',
        tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),
        official_api_tests_executed=any('OfficialApiTests' in t.id() for t in tests),
        passed=result.wasSuccessful() and not result.skipped,versions=versions)
    atomic_json(args.output/'cpu_gate.json',gate)
    print(json.dumps(gate,indent=2),flush=True)
    return 0 if gate['passed'] else 1


if __name__=='__main__': sys.exit(main())
