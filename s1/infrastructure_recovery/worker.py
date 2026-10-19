"""Disposable research entry: original Agent worker, new observers/adapters only."""
import json
from pathlib import Path
import sys

from harness_v2.evidence import atomic_json
from s1.util import sha_file
from . import VERSION
from .environment import research_environment
from .wire import observe_http,audit_requests


def main():
    spec=json.loads(Path(sys.argv[1]).read_text())
    registered=spec['research_infrastructure']
    assert registered['version']==VERSION
    path=Path(registered['environment_admission_path'])
    assert sha_file(path)==registered['environment_admission_sha256']
    admission=json.loads(path.read_text())
    assert admission['eligible'] and admission['instance_id']==spec['instance_id']
    assert admission['base_commit']==spec['base_commit']
    directory=Path(sys.argv[2])
    try:
        with observe_http(directory),research_environment(audit_modules=registered['audit_modules'],task_wheels=spec['wheels_dir']):
            from s1.worker import main as r04_worker
            r04_worker()
    finally:
        # Final gate occurs AFTER supervisor process-tree cleanup, in session.py.
        atomic_json(directory/'http_observer_summary.json',audit_requests(directory))


if __name__=='__main__':main()
