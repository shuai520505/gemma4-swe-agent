"""Final integrity and regression ledger. No network, service or Kaggle execution."""
import hashlib,json
from pathlib import Path
from datetime import datetime,timezone
R=Path(__file__).resolve().parent;D=R.parent;ROOT=D.parents[1]
load=lambda p:json.loads(Path(p).read_bytes())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
manifest=load(D/'PACKAGE_MANIFEST.json')
packages={k:sha(D/'packages'/(k+'.zip'))==v['sha256'] for k,v in manifest['arms'].items()}
assert all(packages.values())
task=load(D/'SMOKE_TASK_LOCK.json')['tasks'][0]
snapshot=sha(D/'assets/snapshots'/task['snapshot_file']);assert snapshot==task['official_snapshot_sha256']
issue=next(r for r in load(D/'ISSUES.agent.json') if r['instance_id']==task['instance_id']);assert hashlib.sha256(issue['problem_statement'].encode()).hexdigest()==task['issue_sha256']
sdk=ROOT/'work/r2-audit/sdk-env/Lib/site-packages/swegemma/harness/verification.py'
assert sha(sdk)==load(D/'evidence/EVALUATOR_IDENTITY.json')['sha256']
ledger=load(R/'REGRESSION_EXECUTIONS.json');assert not ledger['running']
last=load(R/'FOLLOWUP_EXECUTIONS.json')
final={r['stage']:dict(exit_code=r['exit_code'],log=r['log']) for r in ledger['completed'] if r['stage']!='fixture_evidence16'}
final.update({r['name']:dict(exit_code=r['exit_code'],log=r['log']) for r in last})
assert all(r['exit_code']==0 for r in final.values())
out=dict(observed_at_utc=datetime.now(timezone.utc).isoformat(),final_checks=final,earlier_failed_fixture_run_preserved=True,earlier_aggregate_runner_exit=1,reason_for_earlier_failure='Evidence-status label formatting; final17-check rerun exit0',existing_tests=47,legacy_tests=27,infrastructure_tests=6,new_forensic_tests=17,Compiler_packages=4,service_startup_acceptance='NOT_RUN',new_Linux_acceptance='NOT_RUN',new_SaveKernel_requests=0,GPU_requests=0,packages_installed=0,package_hashes_match=packages,task_id=task['instance_id'],Issue_sha256=task['issue_sha256'],snapshot_sha256=snapshot,evaluator_sha256=sha(sdk))
(R/'FINAL_CHECKS.json').write_text(json.dumps(out,indent=2)+'\n')
report=D/'REQUESTS_REGRESSION_REPORT.md'
text=report.read_text(encoding='utf8')
text+='''
## Final actual local results

| Check | Final result | Exact receipt |
|---|---|---|
| Existing47 |PASS, exit0|FOLLOWUP_EXECUTIONS.json / existing47_final.log|
| Legacy27 |PASS, exit0 (440.561s)|REGRESSION_EXECUTIONS.json / regression-logs/legacy27.log|
| Infrastructure6 |PASS, exit0|REGRESSION_EXECUTIONS.json / regression-logs/infrastructure6.log|
| New17 forensic/classifier checks |PASS, exit0|FOLLOWUP_EXECUTIONS.json / fixture17.log|
| Actual Compiler A/B/C/D |PASS, exit0|REGRESSION_EXECUTIONS.json / compiler-work/evidence/SDK_COMPILER.json|

The initial aggregate test runner exited1 because it retains the earlier fixture-status-label failure; the final individual follow-up checks exit0. Its original failure log is preserved. No full legacy suite was rerun to hide that history. FINAL_CHECKS.json records the final ledger and exact package/task/snapshot/evaluator identity checks.
'''
report.write_text(text,encoding='utf8')
print(json.dumps(out))
