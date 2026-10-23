import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
ID='U-RE-V04-EVIDENCE-GUIDED-REPAIR-01'
BASE='cc432feb8de585bd976fa3e0b676365e60b18603'
PACKAGE='u_re.v04.experiments.evidence_guided_repair_01'
CONTROL=ROOT/'u_re/v01/experiments/action_priority_01/candidate_action_v01'
CONTROL_SHA='70af6921a3366e3801efe58fe06586d13189fdf044d4fd998faa62ea7e0fb1c8'
def sha(b):return hashlib.sha256(b).hexdigest()
def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(value if isinstance(value,bytes) else (json.dumps(value,indent=2,ensure_ascii=True)+'\n').encode())
