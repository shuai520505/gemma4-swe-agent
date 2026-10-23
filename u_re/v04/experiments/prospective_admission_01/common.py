import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[3]
BASE='a44cc483a6c114940a65322371dfa87ea5d9dd5e'
ID='U-RE-V04-EGR-PROSPECTIVE-ADMISSION'
PACKAGE='u_re.v04.experiments.prospective_admission_01'
PRIOR=ROOT/'u_re/v04/experiments/evidence_guided_repair_01'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(value if isinstance(value,bytes) else (json.dumps(value,indent=2)+'\n').encode())
