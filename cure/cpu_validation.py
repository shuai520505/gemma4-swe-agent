"""Fresh official Linux CPU gate, separately versioned from r12."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
from . import VERSION
from .mechanisms import run_suite
from harness_v2.evidence import atomic_json


def main(revision, output):
    root = Path(__file__).resolve().parents[1]; output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    plan = json.loads((root / 'cure/registrations' / f'{revision}.json').read_text())
    for name, digest in plan['source_hashes'].items():
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest, name
    legacy = subprocess.run([sys.executable, '-m', 'harness_v2.cpu_validation', str(output / 'legacy')], cwd=root, capture_output=True, text=True, timeout=900)
    (output / 'legacy-runner.log').write_text(legacy.stdout + legacy.stderr)
    os.environ['CURE_CPU_EVIDENCE_DIR'] = str(output / 'request-semantics')
    p = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'cure/tests', '-v'], cwd=root, capture_output=True, text=True, timeout=900)
    (output / 'cure-tests.log').write_text(p.stdout + p.stderr)
    old = json.loads((output / 'legacy/cpu_gate.json').read_text())
    # Test runner return code plus no skips; official semantics test writes its evidence only after all assertions.
    wire = output / 'request-semantics/http-request-cases.json'
    no_skip = 'skipped' not in (p.stdout + p.stderr).lower()
    gate = dict(version=VERSION, revision=revision, kind='official_CPU_mock_HTTP_no_model',
        legacy_tests_run=old['tests_run'], legacy_passed=old['passed'], cure_test_exit_code=p.returncode,
        official_request_semantics_passed=wire.exists(), skipped=0 if no_skip else None,
        passed=legacy.returncode == 0 and old['passed'] and old['tests_run'] == 38 and p.returncode == 0 and wire.exists() and no_skip,
        versions={name: importlib.metadata.version(name) for name in ('swegemma', 'adk-submission', 'google-adk', 'google-genai', 'litellm')},
        source_hashes=plan['source_hashes'])
    atomic_json(output / 'cpu_gate.json', gate)
    run_suite(output / 'mechanisms')
    print(json.dumps({k: v for k, v in gate.items() if k != 'source_hashes'}, indent=2), flush=True)
    return 0 if gate['passed'] else 1


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('revision'); p.add_argument('output', type=Path)
    a = p.parse_args(); sys.exit(main(a.revision, a.output))
