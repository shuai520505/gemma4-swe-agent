"""Fresh eight-task native baseline and identity gate; no model, no Agent."""
import asyncio,json,sys
from pathlib import Path
from harness_v2.evidence import atomic_json
from s1.task_identity import identify,find_data
from .environments import check


def main(output):
 out=Path(output);out.mkdir(parents=True,exist_ok=False)
 spec=json.loads(Path('s2/egv_agenttool_t500_v01/TASK_REUSE_INPUT.json').read_text())
 assert identify(find_data(),spec['task_inputs'])==spec['task_inputs']
 records=[]
 for row in spec['selected']:
  r=asyncio.run(check(row,out/row['instance_id']));records.append(r)
  atomic_json(out/'progress.json',records)
  if not r['cleanup_complete']:break
 gate=dict(passed=len(records)==8 and all(r['eligible'] for r in records),records=records,Agent_runs=0,GPU=False,
  identities_match=True,reference_patch_used=False,scope='Fresh evaluator-only native baselines and exact input hashes. Not algorithm successes.')
 atomic_json(out/'task_admission_gate.json',gate)
 assert gate['passed']
 print('Fresh eight-task baseline gate passed; zero Agent/GPU runs')

if __name__=='__main__':main(sys.argv[1])
