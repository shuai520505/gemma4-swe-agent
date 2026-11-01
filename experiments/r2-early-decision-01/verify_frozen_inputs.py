"""Read-only digest verification of prior study assets."""
import hashlib,json
from pathlib import Path
D=Path(__file__).resolve().parent
files={}
for name in ('FROZEN_INPUT_IDENTITIES.json','HISTORY_ADDITIONAL_IDENTITIES.json'):
    files.update(json.loads((D.parent/'r2-budget-optimization'/name).read_bytes()))
rows=[]
for name,expected in files.items():
    p=Path(name)
    if not p.is_file():
        rows.append(dict(path=name,status='MISSING',expected=expected));continue
    h=hashlib.sha256()
    with p.open('rb') as stream:
        for b in iter(lambda:stream.read(8388608),b''):h.update(b)
    rows.append(dict(path=name,status='PASS' if h.hexdigest()==expected else 'CHANGED',expected=expected,actual=h.hexdigest()))
result=dict(status='PASS' if all(r['status']=='PASS' for r in rows) else 'BLOCKED',count=len(rows),rows=rows)
(D/'FROZEN_INPUT_VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='rows'}))
