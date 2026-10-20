"""Read-only frozen-byte/payload audit; never executes a Notebook cell body."""
import ast
import base64
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import unittest
import zipfile

HERE = Path(__file__).resolve().parent
EARLY = HERE.parents[1]
ROOT = EARLY.parents[1]
sys.path.insert(0, str(ROOT))
from s2.egv_agenttool_t500_early_v01.audit import inspect
from kagglesdk.kaggle_object import TimeDeltaSerializer


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def duration(raw):
    if not isinstance(raw, str) or not re.fullmatch(r'\d+(?:\.\d{1,9})?s', raw):
        raise ValueError('Unknown or malformed wire duration; no inferred correction')
    return Decimal(raw[:-1])


class DurationTests(unittest.TestCase):
    def test_days_and_fractions_preserved(self):
        wire = read(HERE / 'wire_GetAcceleratorQuotaStatistics.json')['response']['gpuQuota']
        for key in ('timeUsed', 'timeReserved', 'totalTimeAllowed'):
            typed = TimeDeltaSerializer._from_dict_value(wire[key])
            self.assertEqual(Decimal(str(typed.total_seconds())), duration(wire[key]))
        self.assertEqual(duration(wire['totalTimeAllowed']), Decimal(108000))
        self.assertEqual(TimeDeltaSerializer._to_dict_value(
            TimeDeltaSerializer._from_dict_value(wire['totalTimeAllowed'])), '21600s')
        self.assertEqual(TimeDeltaSerializer._to_dict_value(
            TimeDeltaSerializer._from_dict_value(wire['timeUsed'])), '20805.644.0s')

    def test_malformed_or_unknown_rejected(self):
        for value in ('20805.644.0s', None, '108000', '-1s', '30 hours'):
            with self.assertRaises(ValueError):
                duration(value)

    def test_resource_calculation(self):
        wire = read(HERE / 'wire_GetAcceleratorQuotaStatistics.json')['response']['gpuQuota']
        balance = duration(wire['totalTimeAllowed']) - duration(wire['timeUsed']) - duration(wire['timeReserved'])
        self.assertEqual(balance, Decimal('87194.356'))
        self.assertGreaterEqual(balance, Decimal(20600))


def audit():
    checks = inspect()
    checkout = subprocess.check_output(['git', '-c', 'core.longpaths=true', 'ls-tree', '-rz', '--full-tree', '272c28401a9932b0d900e40f67ff088fc7eb1c43'], cwd=ROOT)
    approved_crlf = {r['path']: r['unchanged_raw_SHA256'] for r in
                     read(EARLY / 'HISTORICAL_INTEGRITY_FINAL.json')['preexisting_CRLF_checkout_files']}
    historical = {'files_checked': 0, 'approved_preexisting_CRLF': [], 'mismatches': [], 'ZIP_sha256': {}}
    for row in checkout.split(b'\0'):
        if not row:
            continue
        header, name = row.split(b'\t', 1)
        mode, kind, expected = header.decode().split()
        name = name.decode('utf-8')
        assert kind == 'blob', (kind, name)
        raw = (ROOT / name).read_bytes()
        blob = lambda b: hashlib.sha1(b'blob ' + str(len(b)).encode() + b'\0' + b).hexdigest()
        if blob(raw) != expected:
            if approved_crlf.get(name) == sha(raw) and blob(raw.replace(b'\r\n', b'\n')) == expected:
                historical['approved_preexisting_CRLF'].append(name)
            else:
                historical['mismatches'].append(name)
        if name.endswith('.zip'):
            historical['ZIP_sha256'][name] = sha(raw)
        historical['files_checked'] += 1
    assert not historical['mismatches'], historical['mismatches']
    manifest = read(EARLY / 'INTEGRITY_MANIFEST.json')
    drift = [name for name, expected in manifest['files'].items()
             if sha((EARLY / name).read_bytes()) != expected['sha256']]
    assert not drift, drift
    frozen = read(EARLY / 'GPU_DRAFT_FREEZE.json')
    for field, relative in (
        ('protocol_sha256', 'GPU_MECHANISM_PROTOCOL_DRAFT.json'),
        ('notebook_sha256', 'notebooks/gpu-draft/study.ipynb'),
        ('metadata_sha256', 'notebooks/gpu-draft/kernel-metadata.json')):
        assert sha((EARLY / relative).read_bytes()) == frozen[field], relative
    protocol = read(EARLY / 'GPU_MECHANISM_PROTOCOL_DRAFT.json')
    notebook = read(EARLY / 'notebooks/gpu-draft/study.ipynb')
    tree = ast.parse(notebook['cells'][0]['source'])
    assert isinstance(tree.body[0], ast.Raise)
    # Execute ONLY the unconditional first raise, not the rest of the cell.
    try:
        exec(compile(ast.Module(body=[tree.body[0]], type_ignores=[]), '<guard-only>', 'exec'), {})
    except RuntimeError as exc:
        guard = str(exc)
    else:
        raise AssertionError('Draft did not refuse execution')
    payload_assignment = next(n for n in ast.walk(tree) if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == 'payload' for t in n.targets))
    payload = base64.b64decode(ast.literal_eval(payload_assignment.value.args[0]))
    assert sha(payload) == frozen['payload_sha256']
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        assert z.testzip() is None
        assert len(z.namelist()) == len(set(z.namelist()))
        assert all(not PurePosixPath(n).is_absolute() and '..' not in PurePosixPath(n).parts for n in z.namelist())
        assert z.read('s2/early_gpu_protocol.json') == (EARLY / 'GPU_MECHANISM_PROTOCOL_DRAFT.json').read_bytes()
        assert sha(z.read('s2/early_cpu_acceptance.json')) == protocol['CPU_acceptance_sha256']
        source_drift = [n for n, h in protocol['source_hashes'].items() if sha(z.read(n)) != h]
        assert not source_drift, source_drift
        for arm, candidate in protocol['candidates'].items():
            directory = candidate['directory']
            for name, expected in candidate['members'].items():
                assert sha(z.read(directory + '/' + name)) == expected
                assert z.read(directory + '/' + name) == (ROOT / directory / name).read_bytes()
            assert sha((ROOT / directory).parent.joinpath('submission.zip').read_bytes()) == candidate['zip_sha256']
        reg = json.loads(z.read('s1/registration.json'))
        assert reg['wheel_hashes'] == protocol['wheel_hashes']
        assert reg['task_wheel_hashes'] == protocol['task_wheel_hashes']
        for name, expected in reg['source_hashes'].items():
            assert sha(z.read(name)) == expected
    for name, expected in (
        ('CPU_ACCEPTANCE.json', protocol['CPU_acceptance_sha256']),
        ('TASK_SELECTION_PREREGISTRATION.json', protocol['task_registration_sha256']),
        ('results/env01/validation/environment_gate.json', protocol['environment_gate_sha256'])):
        assert sha((EARLY / name).read_bytes()) == expected
    environment = read(EARLY / 'results/env01/validation/environment_gate.json')
    selection = read(EARLY / 'TASK_SELECTION_PREREGISTRATION.json')
    assert protocol['task_inputs'] == selection['task_inputs']
    assert read(EARLY / 'results/env01/wheel_hashes.json') == protocol['wheel_hashes']
    assert read(EARLY / 'results/env01/task_wheel_hashes.json') == protocol['task_wheel_hashes']
    prior_model = read(ROOT / 's2/experiments/t500_agenttool_smoke_01/results/gpu01/model_identity.json')
    assert prior_model['files'] == protocol['model_files']
    metadata = read(HERE / 'prior_gpu_metadata_fresh.json')['result']
    draft_metadata = read(EARLY / 'notebooks/gpu-draft/kernel-metadata.json')
    assert metadata['dockerImage'] == draft_metadata['docker_image']
    assert metadata['modelDataSources'] == draft_metadata['model_sources']
    assert metadata['machineShape'] == draft_metadata['machine_shape'] == 'NvidiaL4'
    assert protocol['candidates']['A']['config'] == protocol['candidates']['B']['config'] == protocol['shared_budget']
    assert not protocol['GPU_authorized'] and not protocol['GPU_executed']
    git = subprocess.check_output(['git', '-c', 'core.longpaths=true', 'status', '--porcelain', '--untracked-files=all'], cwd=ROOT, text=True)
    outside = [line for line in git.splitlines() if str(HERE.relative_to(ROOT).as_posix()) not in line]
    assert not outside, outside
    return {
        'queried_at_utc': datetime.now(timezone.utc).isoformat(), 'passed': True,
        'entire_baseline_checkout': historical,
        'existing_acceptance_recheck': checks, 'frozen_manifest_files_checked': len(manifest['files']),
        'frozen_manifest_drift': drift, 'payload_source_bindings_checked': len(protocol['source_hashes']),
        'payload_sha256': sha(payload), 'payload_crc': True, 'payload_source_drift': source_drift,
        'protocol_and_cpu_and_environment_bindings': True, 'task_input_identities': protocol['task_inputs'],
        'runs': protocol['runs'], 'shared_budget': protocol['shared_budget'],
        'model': protocol['model'], 'model_manifest_sha256': sha(json.dumps(protocol['model_files'], sort_keys=True).encode()),
        'model_files_match_prior_real_smoke': True, 'docker_and_model_reference_match_saved_smoke': True,
        'model_wheel_count': len(protocol['wheel_hashes']), 'task_wheel_count': len(protocol['task_wheel_hashes']),
        'environment_gate': environment, 'guard_refusal': guard,
        'remote_gpu_draft_saved': False,
        'remote_gpu_draft_saved_basis': 'No matching ref in exhausted 165-item own saved-Notebook inventory; interactive/private-inaccessible sessions cannot be excluded.',
        'current_mounted_model_and_wheel_bytes_rechecked': False,
        'new_GPU_started': False, 'new_submission': False,
        'execution_authorization': 'NOT_GRANTED', 'algorithm_evidence': 'EarlyEGV real Gemma NOT_RUN',
    }


if __name__ == '__main__':
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(DurationTests)
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    (HERE / 'DURATION_REGRESSION.log').write_text(stream.getvalue(), encoding='utf-8')
    assert result.wasSuccessful()
    observed = audit()
    (HERE / 'READINESS_AUDIT.json').write_text(json.dumps(observed, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: observed[k] for k in ('passed', 'frozen_manifest_files_checked', 'payload_source_bindings_checked', 'payload_crc', 'new_GPU_started')}, indent=2))
