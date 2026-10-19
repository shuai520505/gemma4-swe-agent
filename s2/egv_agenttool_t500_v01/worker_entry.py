"""Research-only entry, original native Phase2 and cancellation observer intact."""
import json
from pathlib import Path
import sys
from s1.util import sha_file
from s1.infrastructure_recovery.wire import observe_http,audit_requests
from s1.verifier_v3.environment import research_environment
from harness_v2.evidence import atomic_json


def main():
    spec=json.loads(Path(sys.argv[1]).read_text());entry=spec['research_infrastructure']
    admission=Path(entry['environment_admission_path'])
    assert sha_file(admission)==entry['environment_admission_sha256']
    baseline=json.loads(admission.read_text())
    assert baseline['eligible'] and baseline['instance_id']==spec['instance_id'] and baseline['base_commit']==spec['base_commit']
    directory=Path(sys.argv[2])
    try:
        with observe_http(directory),research_environment(audit_modules=entry['audit_modules'],task_wheels=spec['wheels_dir']):
            from .worker import main as native_main
            native_main()
    finally:atomic_json(directory/'http_observer_summary.json',audit_requests(directory))


if __name__=='__main__':main()
