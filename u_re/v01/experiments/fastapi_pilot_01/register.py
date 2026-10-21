"""Create prospective FastAPI-only policy from immutable mechanism02 inputs."""
import hashlib
import json
from pathlib import Path
import subprocess
from datetime import datetime, timezone

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
BASE='582a016fb0c836222b6a3d653bb732e0c5e6130d'
PREVIOUS=HERE.parent/'mechanism_02'


def sha(data):return hashlib.sha256(data).hexdigest()


def write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    data=data if isinstance(data,bytes) else (json.dumps(data,indent=2)+'\n').encode() if not isinstance(data,str) else data.encode()
    if path.exists():
        assert path.read_bytes()==data,'Do not overwrite: '+str(path)
    else:
        with path.open('xb') as f:f.write(data)


def main():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==BASE
    rows=json.loads((PREVIOUS/'RANKED_POOL.json').read_bytes())['rows']
    exclusions=json.loads((PREVIOUS/'EXCLUSION_LEDGER_V02.json').read_bytes())
    ids=exclusions['excluded_task_ids']
    assert len(ids)==79 and len(rows)==50 and len({r['instance_id'] for r in rows})==50
    assert {r['repo'] for r in rows}=={'fastapi/fastapi'}
    assert not {r['instance_id'] for r in rows}.intersection(ids)
    for name in ('RANKED_POOL.json','EXCLUSION_LEDGER_V02.json','TASK_POOL_METADATA.json'):
        raw=(PREVIOUS/name).read_bytes()
        old=subprocess.check_output(['git','show',BASE+':'+(PREVIOUS/name).relative_to(ROOT).as_posix()],cwd=ROOT)
        assert raw==old
        write(HERE/name,raw)
    write(HERE/'EXCLUSION_AUDIT.json',dict(source_commit=BASE,source='u_re/v01/experiments/mechanism_02/EXCLUSION_LEDGER_V02.json',
        excluded_task_ids=ids,excluded_count=79,available_count=50,original_metadata_count=129,
        exclusion_source_sha256=sha((PREVIOUS/'EXCLUSION_LEDGER_V02.json').read_bytes()),
        rank_source_sha256=sha((PREVIOUS/'RANKED_POOL.json').read_bytes()),
        no_exclusions_removed=True,no_exposure_reinterpretation=True,uncertainty_retained=True,
        scope='Inherited used/reserved/analyzed/uncertain labels remain as originally audited; exclusion does not imply model execution'))
    policy=dict(experiment_id='U-RE-V01-FASTAPI-PILOT-01',status='DRAFT_NOT_EXECUTED',base_commit=BASE,
        registered_at_utc=datetime.now(timezone.utc).isoformat(),
        independent_of=['U-RE-V01-MECHANISM-01','U-RE-V01-MECHANISM-02'],
        selection_algorithm=dict(rank='reuse exact mechanism02 RANKED_POOL.json bytes; ascending SHA256 U-RE-V0.1-MECHANISM-02:17:+instance_id',
            max_cpu_checks=8,select='First two BASELINE_ELIGIBLE distinct instance_id values in frozen order; same FastAPI repository allowed',
            only_design_change='Drop distinct-repository requirement in a separately registered FastAPI-only pilot',
            all_passing_baseline='NON_DISCRIMINATING; do not infer repair task from exit0',
            environment_failures='Record explained supported dependency/fixture blocks and continue rank; unknown errors or evidence/source/cleanup failures STOP',
            prohibit=['difficulty ranking','test-count ranking','reference repair','model outcome selection','candidate edits','task substitutions','extending max8']),
        admission=dict(path='unchanged native swegemma verify_task with original snapshot/base/evaluator-only overlay and empty Agent patch',
            evidence=['native TaskResult','JUnit before sandbox stop','native stdout/stderr','workspace provenance','unchanged source/test hashes','process/sandbox cleanup'],
            dependency_installation='approved frozen offline Wheelhouse only; no extra dependencies',
            provenance_scope='Module execution confirms workspace import, not complete behavioral coverage'),
        candidates=json.loads((PREVIOUS/'CANDIDATE_INTEGRITY.json').read_bytes()),
        budget=dict(agent_seconds=300,counted_tools=60,command_seconds=120),
        future_order=['A','B','B','A'],future_arms=dict(A='NoEGV',B='Full'),
        same_repository_dependence='Flag Issue/target/test-contract overlap after selection without subjective replacement; two tasks are not independent repository samples',
        execution=dict(execute=False,gpu_authorized=False,formal_submission=False,Agent_runs=0,model_calls=0),
        source_hashes={n:sha((HERE/n).read_bytes()) for n in ['register.py','screen.py','gpu_execution_stub.py','EXCLUSION_AUDIT.json','EXCLUSION_LEDGER_V02.json','RANKED_POOL.json','TASK_POOL_METADATA.json']})
    write(HERE/'SELECTION_PROTOCOL.json',policy)
    write(HERE/'SELECTION_PROTOCOL.md','''# U-RE-V01-FASTAPI-PILOT-01 prospective selection

Independent FastAPI-only scope; no claim of cross-project generalization. Preserve U-RE-01/02 blocked protocols. Inherit all79 conservative exclusions and exact50 ranked metadata rows. Never reinterpret used/reserved/analyzed/uncertain reasons to enlarge the pool.

Before any native CPU baseline commit this JSON, screening source, rank/exclusion inventory and source hashes. Visit exact existing rank, max8 actual checks, choose first two eligible distinct instance IDs. Same repository is allowed. Do not rank by issue difficulty, tests, expected EGV benefit or repair outcomes. Do not read reference repairs. Record every attempt and leave unexecuted results null/NOT_RUN.

Use original native verify_task, empty Agent patch and original evaluator-only test overlay in isolated clean CPU sandbox. Ordinary assertions are eligible only with intact JUnit, source/provenance and cleanup. All-pass is non-discriminating. Known evidenced environment blockers may be rejected; unexplained errors/evidence loss/identity drift trigger STOP. No test, Verifier, dependency source or candidate modifications. Max8 without two tasks => TASK_ADMISSION_BLOCKED, no sample expansion.

After selection bind Issue/base/snapshot/test-overlay/task-record hashes. Inspect same-Issue, target-path and test-contract overlap only to label dependency risk, without replacing a selected task. Future order A→B then B→A; independent sessions/workspaces/Verifier sandboxes, no cross-arm or cross-task Trace/Patch/output transfer. NoEGV retains ordinary tests. Four future model runs remain NOT_AUTHORIZED.
''')
    tracked=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().strip('\0').split('\0')
    write(HERE/'evidence/INITIAL_HISTORY.json',{n:sha((ROOT/n).read_bytes()) for n in tracked})
    write(HERE/'.gitattributes','* -text whitespace=cr-at-eol\n')
    write(HERE/'.gitignore','__pycache__/\n_local/\nresults/*/download/\n')
    print(json.dumps(dict(pool=len(rows),excluded=len(ids),history_files=len(tracked),CPU_baselines_run=0)))


if __name__=='__main__':main()
