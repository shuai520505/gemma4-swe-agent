"""Read/hash prior study and protected assets without rewriting their receipts."""
import hashlib,json
from pathlib import Path
D=Path(__file__).resolve().parent;old=D.parent/'r2-early-decision-01'
def identities():
    files=[p for p in old.iterdir() if p.is_file() and p.suffix in ['.py','.md','.json','.diff']]
    files += list((old/'candidates').glob('*.zip'))+[old/'gpu-output/r2a-real-gpu-01.zip']
    return {str(p.resolve()):hashlib.file_digest(p.open('rb'),'sha256').hexdigest() for p in files}
p=D/'PRIOR_STUDY_IDENTITIES.json'
if p.exists():
    expected=json.loads(p.read_bytes());actual=identities()
    assert expected==actual,'Prior study identity changed'
    print(json.dumps(dict(status='PASS',files=len(actual))))
else:
    v=identities();p.write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(dict(status='FROZEN_READ_ONLY',files=len(v))))
protected={}
for name in ['FROZEN_INPUT_IDENTITIES.json','HISTORY_ADDITIONAL_IDENTITIES.json']:
    protected.update(json.loads((D.parent/'r2-budget-optimization'/name).read_bytes()))
bad=[name for name,expected in protected.items() if not Path(name).is_file() or hashlib.file_digest(Path(name).open('rb'),'sha256').hexdigest()!=expected]
assert not bad,'Protected historical inputs changed'
(D/'PROTECTED_ASSET_VERIFICATION.json').write_text(json.dumps(dict(status='PASS',protected_historical_assets=len(protected),prior_study_assets=len(identities()),prior_study_manifest_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),historical_receipts_rewritten=False),indent=2)+'\n')
