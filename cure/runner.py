"""Run one explicitly requested research task after a matching official CPU gate."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from harness_v2.evidence import atomic_json, bundle
from harness_v2.supervisor import supervise
from .runtime_config import ResearchConfig
from . import VERSION


def require_gate(path, root):
    gate = json.loads(Path(path).read_text(encoding='utf-8'))
    if gate.get('version') != VERSION or gate.get('passed') is not True or gate.get('skipped') != 0:
        raise ValueError('Matching official CPU gate required')
    required = {'cure/worker.py', 'cure/request_guard.py', 'cure/runtime_config.py', 'cure/observer.py', 'harness_v2/supervisor.py'}
    if not required.issubset(gate.get('source_hashes', {})):
        raise ValueError('Incomplete CPU source registration')
    for name, digest in gate['source_hashes'].items():
        if hashlib.sha256((Path(root) / name).read_bytes()).hexdigest() != digest:
            raise ValueError('CPU-tested research source changed: ' + name)
    if not gate.get('official_request_semantics_passed') or gate.get('legacy_tests_run') != 38:
        raise ValueError('Official request semantics and all 38 legacy tests required')
    return gate


def run(spec_path, directory, gate_path):
    root = Path(__file__).resolve().parents[1]
    if Path(directory).exists() or Path(directory).with_suffix('.zip').exists():
        raise FileExistsError('A fresh research run directory and archive are required')
    require_gate(gate_path, root)
    spec = json.loads(Path(spec_path).read_text(encoding='utf-8'))
    config = ResearchConfig(**spec['research_config'])
    # Isolated supervisor refuses reused directories; worker verifies candidate/task hashes.
    try:
        return supervise([sys.executable, '-m', 'cure.worker', str(Path(spec_path).resolve()), str(Path(directory).resolve())],
            directory, outer_seconds=config.outer_seconds, stage_caps=config.stage_caps, cwd=root)
    finally:
        if (Path(directory) / 'controller_started.json').exists():
            bundle(directory)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('spec', type=Path); p.add_argument('directory', type=Path)
    p.add_argument('--cpu-gate', type=Path, required=True)
    a = p.parse_args(); print(json.dumps(run(a.spec, a.directory, a.cpu_gate), indent=2))
