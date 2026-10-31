import json
import os
from pathlib import Path
import shlex
from dataclasses import asdict

from harness_v2.evidence import Journal
from swegemma.harness.container_setup import extract_snapshot
from egrd.v032.evaluate import source_identity
from .sandbox import SubprocessManager
from .common import sha,write

def evaluate(binding,out,patch_text=None):
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    manager=SubprocessManager(journal=Journal(out),base_dir=out/'roots',task_wheels=Path(binding['wheels']))
    task=binding['task'];data=Path(binding['data'])
    result=dict(official_native_resolved=None,canonical_swebench_resolved=None,cleanup=False,
                patch_present=bool(patch_text),patch_sha256=sha(patch_text.encode()) if patch_text else None)
    try:
        sid=manager.start();entry=manager.sandboxes[sid];workspace=entry['workspace']
        extract_snapshot(manager,sid,Path(binding['snapshot']))
        original=source_identity(workspace);assert original==binding['base_source_identity']
        protected=entry['root']/'evaluation';protected.mkdir(mode=0o755)
        programs={n:Path(p).read_bytes() for n,p in binding['evaluation_programs'].items()} if 'evaluation_programs' in binding else {'probe.py':(data/task['diagnostic_path']).read_bytes(),'common.py':(data/'diagnostics/common.py').read_bytes()}
        expected={n:sha(b) for n,b in programs.items()}
        for n,b in programs.items():(protected/n).write_bytes(b);(protected/n).chmod(0o444)
        protected.chmod(0o555)
        if patch_text:
            path=out/'candidate.patch';path.write_text(patch_text,encoding='utf8');manager.copy_to(sid,path,'/tmp/candidate.patch')
            checked=manager.exec(sid,'git apply --check /tmp/candidate.patch',timeout=30)
            result['patch_applicable']=checked.exit_code==0
            if checked.exit_code:
                result['apply_error']=asdict(checked);return result
            applied=manager.exec(sid,'git apply /tmp/candidate.patch',timeout=30);assert applied.exit_code==0
        before=source_identity(workspace)
        probe=manager.exec(sid,binding.get('evaluation_command','EGRD_SOURCE=/workspace EGRD_RESULT_PATH=/tmp/probe.json python3 /evaluation/probe.py'),timeout=90)
        result['execution']=asdict(probe)
        try:receipt=json.loads(manager.read_file(binding.get('evaluation_receipt','/tmp/probe.json')))
        except Exception as exc:receipt={};result['receipt_error']=type(exc).__name__
        result['receipt']=receipt
        result['target_passed']=receipt.get('classification')=='CHECK_PASS_NON_DISCRIMINATING' and probe.exit_code==0
        result['target_failed']=receipt.get('classification')=='TARGET_BEHAVIOR_FAILURE'
        result['positive_controls_passed']=receipt.get('controls_passed') is True
        denied=manager.exec(sid,"python3 -c "+shlex.quote("from pathlib import Path\ntry:\n Path('/evaluation/probe.py').write_text('x')\nexcept PermissionError:\n print('DENIED')\nelse:\n raise AssertionError('Trusted check writable')"),timeout=10)
        result['check_write_denied']=denied.exit_code==0 and 'DENIED' in denied.stdout
        result['check_unchanged']=all(sha((protected/n).read_bytes())==h for n,h in expected.items())
        result['source_unchanged_by_checks']=source_identity(workspace)==before
        assert result['check_write_denied'] and result['check_unchanged'] and result['source_unchanged_by_checks']
        result['base_source_identity']=original;result['tested_source_identity']=before
        names=manager.exec(sid,'git add -N . && git diff --name-only HEAD',timeout=30)
        result['changed_files']=names.stdout.strip().splitlines()
        result['scoped_development_pass']=bool(patch_text and result['target_passed'] and result['positive_controls_passed'])
        result['scope']=binding.get('evaluation_scope','Original Issue-grounded owned target and controls; broader regression NOT_RUN; semantic review required')
        return result
    finally:
        manager.cleanup_all()
        result['cleanup']=not manager.sandboxes and all(not Path(e['lease']).exists() for e in manager.entries)
        result['cleanup_records']=manager.cleanup_records
        write(out/'DEVELOPMENT_RESULT.json',result)
