"""Independent context-budget pilot, safe metadata only in Git."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
ID='U-RE-V03-CONTEXT-BUDGET-01'
PACKAGE='u_re.v03.experiments.context_budget_01'
BASE='e3fe17d56c05b6a52442b329450dcd88d0c80bcc'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes((json.dumps(value,indent=2,ensure_ascii=True)+'\n').encode())
