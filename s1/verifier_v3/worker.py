import json
from pathlib import Path
import sys
from harness_v2.evidence import atomic_json
from s1.util import sha_file
from s1.infrastructure_recovery.wire import observe_http,audit_requests
from . import VERSION
from .environment import research_environment


def main():
    spec=json.loads(Path(sys.argv[1]).read_text());registered=spec['research_infrastructure']
    assert registered['version']==VERSION
    admission=Path(registered['environment_admission_path'])
    assert sha_file(admission)==registered['environment_admission_sha256']
    data=json.loads(admission.read_text());assert data['eligible']
    assert data['instance_id']==spec['instance_id'] and data['base_commit']==spec['base_commit']
    directory=Path(sys.argv[2])
    try:
        with observe_http(directory),research_environment(audit_modules=registered['audit_modules'],task_wheels=spec['wheels_dir']):
            from s1.worker import main as native_worker
            native_worker()
    finally:atomic_json(directory/'http_observer_summary.json',audit_requests(directory))


if __name__=='__main__':main()
