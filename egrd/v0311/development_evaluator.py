"""Trusted, separately confined development checks; never Native/SWE-bench scoring."""
import json
import os
from pathlib import Path
import shlex
from dataclasses import asdict

from harness_v2.evidence import Journal
from swegemma.harness.container_setup import extract_snapshot
from .sandbox_adapter import SubprocessManager
from egrd.v031.prepare import sha,write


def source_identity(source,exclude=('.git',)):
    source=Path(source).resolve();rows={}
    for path in sorted(source.rglob('*')):
        rel=path.relative_to(source)
        if rel.parts[0] in exclude:continue
        if path.is_symlink():
            assert path.resolve().is_relative_to(source),'Source symlink escapes workspace'
            rows[rel.as_posix()]=dict(link=os.readlink(path))
        elif path.is_file():rows[rel.as_posix()]=dict(sha256=sha(path.read_bytes()))
    return sha(json.dumps(rows,sort_keys=True).encode())


def evaluate(task,data,out,snapshot,wheels,regression_program,patch_text=None):
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    manager=SubprocessManager(journal=Journal(out),base_dir=out/'trusted-roots',task_wheels=wheels)
    result=dict(official_native_resolved=None,canonical_swebench_resolved=None,correctness='UNKNOWN',
        cleanup=False,production_behavior_changed=None,patch_applicable=None)
    try:
        sid=manager.start();entry=manager.sandboxes[sid];workspace=entry['workspace']
        extract_snapshot(manager,sid,snapshot)
        original=source_identity(workspace);result['original_source_sha256']=original
        lock=json.loads((Path(__file__).parents[1]/'v031/TASK_IDENTITY_LOCK.json').read_bytes())
        assert original==lock['source_tree_before']
        evaluation=entry['root']/'evaluation';evaluation.mkdir(mode=0o755)
        protected={}
        for name,body in {'probe.py':(data/task['diagnostic_path']).read_bytes(),
            'common.py':(data/'diagnostics/common.py').read_bytes(),
            'regression.py':Path(regression_program).read_bytes()}.items():
            path=evaluation/name;path.write_bytes(body);path.chmod(0o444);protected[name]=sha(body)
        evaluation.chmod(0o555)
        result['submitted_patch_sha256']=sha(patch_text.encode()) if patch_text is not None else None
        if patch_text is not None:
            patch_file=out/'submitted.patch';patch_file.write_bytes(patch_text.encode())
            manager.copy_to(sid,patch_file,'/tmp/submitted.patch')
            checked=manager.exec(sid,'git apply --check /tmp/submitted.patch',timeout=30)
            result['patch_applicable']=checked.exit_code==0
            if not result['patch_applicable']:
                result['patch_error']=checked.stderr;return result
            applied=manager.exec(sid,'git apply /tmp/submitted.patch',timeout=30)
            assert applied.exit_code==0
        tested=source_identity(workspace);result['tested_source_sha256']=tested
        if patch_text is not None:
            import ast
            names=manager.exec(sid,'git diff --name-only',timeout=10)
            changed=names.stdout.strip().splitlines()
            assert names.exit_code==0 and changed==['django/contrib/auth/forms.py'],changed
            before=manager.exec(sid,'git show HEAD:django/contrib/auth/forms.py',timeout=10)
            after=(workspace/'django/contrib/auth/forms.py').read_text()
            assert before.exit_code==0 and ast.dump(ast.parse(before.stdout))==ast.dump(ast.parse(after))
            result['changed_production_files']=changed
            result['Python_AST_unchanged']=True
            result['production_behavior_changed']=False
            result['repair_success']=False
        result['probe_program_sha256']=protected['probe.py']
        probe=manager.exec(sid,'EGRD_SOURCE=/workspace EGRD_RESULT_PATH=/tmp/probe.json python3 /evaluation/probe.py',timeout=60)
        receipt=json.loads(manager.read_file('/tmp/probe.json'))
        result['target_receipt']=receipt;write(out/'probe.json',receipt)
        result['diagnostic']=asdict(probe)
        result['target_probe_passed']=receipt['classification']=='CHECK_PASS_NON_DISCRIMINATING'
        result['original_failing_probe_still_fails']=receipt['classification']=='TARGET_BEHAVIOR_FAILURE'
        result['positive_controls_passed']=receipt['controls_passed']
        regression=manager.exec(sid,'EGRD_SOURCE=/workspace python3 /evaluation/regression.py',timeout=60)
        result['bounded_regression']=asdict(regression)
        permission=manager.exec(sid,"python3 -c "+shlex.quote(
            "from pathlib import Path\ntry:\n Path('/evaluation/probe.py').write_text('tamper')\nexcept PermissionError:\n print('TRUSTED_PROBE_WRITE_DENIED')\nelse:\n raise AssertionError('Trusted file writable')"),timeout=10)
        assert permission.exit_code==0 and 'TRUSTED_PROBE_WRITE_DENIED' in permission.stdout
        result['trusted_probe_write_denied']=True
        result['trusted_probe_unchanged']=all(sha((evaluation/n).read_bytes())==h for n,h in protected.items())
        assert result['trusted_probe_unchanged']
        result['source_after_tests_sha256']=source_identity(workspace)
        result['tests_did_not_change_source']=tested==result['source_after_tests_sha256']
        assert result['tests_did_not_change_source']
        result['source_changed_from_original']=tested!=original
        result['environment_warnings']=probe.stderr
        result['evaluation_sandbox']='Separate non-root chroot; no active Agent; readonly root-owned probe; no host mounts/network/proc'
        return result
    finally:
        manager.cleanup_all()
        result['cleanup']=not manager.sandboxes and all(r['root_removed'] for r in manager.cleanup_records) and all(not Path(e['lease']).exists() for e in manager.entries)
        result['cleanup_records']=manager.cleanup_records
        write(out/'DEVELOPMENT_RESULT.json',result)
