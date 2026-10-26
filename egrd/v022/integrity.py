"""Bind preparation files and read-only dependencies; no execution permission."""
import json
import platform
import zipfile
import zlib

from .build import HERE, ROOT, frozen_write, sha, build
from .task_pool import build as freeze_pool
from .freeze_protocol import freeze
from egrd.v021.interface_sources import pinned_sources, WHEELS


REFERENCES = (
    'submission.zip', 'meer/v01/submission_A.zip', 'meer/v01/submission_B.zip',
    'meer/v01/submission_C.zip', 'meer/v01/build.py', 'meer/v01/verify.py',
    'meer/v01/GPU_EXPERIMENT_PROTOCOL.md', 'meer/v01/CANDIDATE_MANIFEST.json',
    'meer/v01/OFFICIAL_SOURCE_PINS.json',
    'meer/v01/gpu01/authorized02/FINAL_DECISION.md',
    'meer/v01/gpu01/authorized02/MECHANISM_EVENTS.json',
    'egrd/v021/FINAL_DECISION.md', 'egrd/v021/ARCHITECTURE_DECISION.md',
    'egrd/v021/OFFICIAL_DEPLOYMENT_MATRIX.md',
    'egrd/v021/REPRODUCTION_DEPLOYMENT_FEASIBILITY.md',
    'egrd/v021/NEXT_EXPERIMENT.md', 'egrd/v021/interface_sources.py',
)


def record(raw):
    return dict(sha256=sha(raw), bytes=len(raw))


def manifest():
    build()
    freeze_pool()
    freeze()
    _, pins = pinned_sources()
    wheels = {}
    for filename, value in pins.items():
        wheels[filename] = dict(sha256=value['sha256'], members={
            name: dict(sha256=info['sha256'], lines=info['lines'])
            for name, info in value['members'].items()})
    with zipfile.ZipFile(WHEELS / 'swegemma-0.2.11-py3-none-any.whl') as wheel:
        for name in ('swegemma/tools/workspace.py', 'swegemma/tools/execution.py'):
            raw = wheel.read(name)
            wheels['swegemma-0.2.11-py3-none-any.whl']['members'][name] = dict(
                **record(raw), lines=len(raw.splitlines()))
    files = {
        path.relative_to(HERE).as_posix(): record(path.read_bytes())
        for path in sorted(HERE.rglob('*'))
        if path.is_file() and '__pycache__' not in path.parts
        and path.name != 'INTEGRITY_MANIFEST.json'
    }
    return dict(schema='EGRD_V022_PREPARATION_INTEGRITY_V1',
        source_base_PR35='765530b39a7666a78ece099756fac925a932c617',
        scope='Preparation only; no new native admission or full Compiler execution',
        files=files,
        read_only_dependencies={name: record((ROOT / name).read_bytes()) for name in REFERENCES},
        official_wheels=wheels,
        build_runtime=dict(python=platform.python_version(), zlib=zlib.ZLIB_RUNTIME_VERSION),
        excludes=['this manifest (self-hash)', '__pycache__'],
        raw_private_records_index='PREPARATION_RECORDS.json')


if __name__ == '__main__':
    result = manifest()
    frozen_write(HERE / 'INTEGRITY_MANIFEST.json',
        (json.dumps(result, indent=2, sort_keys=True) + '\n').encode())
    print('Verified candidate/pool/lock replay and', len(result['files']), 'preparation files.')
