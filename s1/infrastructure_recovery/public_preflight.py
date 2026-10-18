"""New task CPU readiness: original baseline tests only, no repair/reference Patch."""
import json
from pathlib import Path
import shlex
import traceback
from harness_v2.evidence import Journal,atomic_json
from s1.task_identity import identify,find_data
from .environment import SubprocessManager,install_editable


def check(output):
    from swegemma.models import load_tasks
    from swegemma.deduplication import resolve_task_snapshot_paths
    from swegemma.harness.container_setup import extract_snapshot
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    plan=json.loads(Path(__file__).with_name('next_experiment_plan.json').read_text())
    data=find_data();ids=[r['instance_id'] for r in plan['pairs']]
    tasks={t.instance_id:t for t in load_tasks(data/'tasks.jsonl') if t.instance_id in ids}
    atomic_json(output/'task_inputs.json',identify(data,ids))
    reports=[]
    for row in plan['pairs']:
        task=tasks[row['instance_id']];directory=output/task.instance_id
        manager=SubprocessManager(journal=Journal(directory),base_dir=directory/'sandboxes',
            audit_modules=row['audit_modules'],timeout_seconds=180,task_wheels=data/'wheels')
        sid=None;report=dict(instance_id=task.instance_id,base_commit=task.base_commit,eligible=False,
            scope='CPU import and original public baseline target-file tests only; no evaluation test patch')
        try:
            assert task.base_commit==row['base_commit']
            sid=manager.start()
            snapshot,base,patch=resolve_task_snapshot_paths(data/'snapshots',task.instance_id,task.repo)
            extract_snapshot(manager,sid,snapshot,base_snapshot_path=base,patch_path=patch)
            install_editable(manager,sid)
            probe='python3 -c '+shlex.quote('import '+row['audit_modules'][0]+'; print('+row['audit_modules'][0]+'.__file__)')
            imported=manager.exec(sid,probe)
            atomic_json(directory/'import_probe.json',dict(exit_code=imported.exit_code,stdout=imported.stdout,stderr=imported.stderr))
            workspace=manager.sandboxes[sid]['workspace']
            source_ok=imported.exit_code==0 and Path(imported.stdout.strip()).resolve().is_relative_to(workspace)
            # The official Task API supplies paths; no contents of evaluation
            # patches or reference solutions are copied into this research plan.
            targets=[name for name in task.test_files if name.endswith('.py') and Path(name).name!='conftest.py']
            assert all((workspace/name).resolve().is_relative_to(workspace.resolve()) for name in targets)
            assert targets and all((workspace/name).is_file() for name in targets),'Baseline target files missing'
            command='PYTHONSAFEPATH=1 PYTHONNOUSERSITE=1 python3 -s -m pytest '+ ' '.join(shlex.quote(n) for n in targets)+' -p no:anyio -o timeout=0 -o python_classes="Test* *Test" -q'
            result=manager.exec(sid,command,timeout=180)
            atomic_json(directory/'public_baseline_tests.json',dict(command=command,exit_code=result.exit_code,stdout=result.stdout,stderr=result.stderr))
            report.update(eligible=source_ok and result.exit_code==0,source_import_verified=source_ok,
                original_test_targets=targets,public_baseline_exit_code=result.exit_code)
        except Exception as exc:
            report.update(error=repr(exc),traceback=traceback.format_exc())
        finally:
            manager.cleanup_all()
            report['cleanup_complete']=not manager.sandboxes and not list((directory/'sandboxes').glob('swegemma_sandbox_*'))
            report['eligible']=report['eligible'] and report['cleanup_complete']
            atomic_json(directory/'environment_admission.json',report)
            reports.append(report)
    atomic_json(output/'environment_gates.json',reports)
    return reports
