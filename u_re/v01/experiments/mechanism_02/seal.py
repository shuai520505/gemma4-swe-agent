"""Create once, or check, the blocked study's byte manifest. No external work."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
MANIFEST = HERE / 'INTEGRITY_MANIFEST.json'
IGNORED = {'__pycache__', '_local', 'download', '.pytest_cache'}
PINS = {
    'noegv': '2705679a74456937d8c63127fc34df9c99a28446f9bd23c23d56650b91602608',
    'full': '887da066341bb1278ba298894f488bba8e7a3bd09ae5f4417e36a1a51f8ad821',
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def describe():
    inherited = json.loads((HERE / 'evidence/INITIAL_HISTORY.json').read_text())
    changed = [name for name, expected in inherited.items()
               if not (ROOT / name).is_file() or digest(ROOT / name) != expected]
    if changed:
        raise RuntimeError('Inherited byte drift: ' + repr(changed))
    candidates = {}
    for arm, expected in PINS.items():
        path = ROOT / 'u_re/v01' / ('submission_' + arm + '.zip')
        if digest(path) != expected:
            raise RuntimeError('Frozen candidate drift: ' + arm)
        with zipfile.ZipFile(path) as archive:
            if archive.testzip() is not None:
                raise RuntimeError('Candidate CRC error: ' + arm)
            members = {n: hashlib.sha256(archive.read(n)).hexdigest()
                       for n in archive.namelist()}
        candidates[arm] = {'path': path.relative_to(ROOT).as_posix(),
                           'sha256': expected, 'members': members}
    files = {p.relative_to(HERE).as_posix(): digest(p)
             for p in sorted(HERE.rglob('*')) if p.is_file() and p != MANIFEST
             and not (set(p.relative_to(HERE).parts) & IGNORED)}
    return {
        'experiment_id': 'U-RE-V01-MECHANISM-02',
        'status': 'TASK_ADMISSION_BLOCKED',
        'base_commit': '794e5fc3b487b0d7a57002268fac88aa12a34851',
        'selection_commit': 'ac20c4745027c6068571292898b45c4ea0cfb630',
        'CPU_build_commit': '98efddb72733f2b76aefc6a340a513494a0b9527',
        'inherited_files_verified': len(inherited),
        'inherited_hash_inventory': 'evidence/INITIAL_HISTORY.json',
        'candidates': candidates,
        'native_baselines_run': 0,
        'CPU_save_requests': 0,
        'GPU_runs': 0,
        'Gemma_inference_runs': 0,
        'formal_submissions': 0,
        'selected_tasks': [],
        'local_policy_readiness_tests': 13,
        'local_tests_are_native_baselines': False,
        'manifest_self_excluded': True,
        'excluded_directory_names': sorted(IGNORED),
        'file_count': len(files),
        'files': files,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--create', action='store_true')
    args = parser.parse_args()
    actual = describe()
    if args.create:
        with MANIFEST.open('x', encoding='utf-8', newline='\n') as out:
            out.write(json.dumps(actual, indent=2) + '\n')
    else:
        expected = json.loads(MANIFEST.read_text())
        if actual != expected:
            raise RuntimeError('Manifest mismatch; do not overwrite an existing seal')
    print(json.dumps({'manifest_sha256': digest(MANIFEST),
                      'new_files_verified': actual['file_count'],
                      'inherited_files_verified': actual['inherited_files_verified'],
                      'native_baselines_run': actual['native_baselines_run'],
                      'status': actual['status']}))


if __name__ == '__main__':
    main()
