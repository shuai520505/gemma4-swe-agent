"""Recheck candidate strategy/config isolation without invoking a model."""
import difflib,hashlib,json,zipfile
from pathlib import Path
D=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
packages={}
for n in ('R2','A'):
    p=D/'candidates'/(n+'.zip')
    with zipfile.ZipFile(p) as z:
        assert z.testzip() is None
        packages[n]={'zip_sha256':sha(p.read_bytes()),'files':{k:z.read(k) for k in z.namelist()}}
assert packages['R2']['zip_sha256']=='af918c1a65aeb211298f13a69b5b789ae6b086974922c80469df87d902eb98d5'
assert set(packages['R2']['files'])==set(packages['A']['files'])
changed=[n for n in packages['R2']['files'] if packages['R2']['files'][n]!=packages['A']['files'][n]]
assert changed==['prompts/system.md']
old=packages['R2']['files']['prompts/system.md'].decode();new=packages['A']['files']['prompts/system.md'].decode()
spec=json.loads((D.parent/'r2-budget-optimization/candidate-a-design/CANDIDATE_A_POLICY_SPEC.json').read_bytes())
assert old.replace(spec['old_exact'],spec['new_exact'],1)==new
assert old.split('# DEADLINE-AWARE FINALIZATION',1)[1]==new.split('# DEADLINE-AWARE FINALIZATION',1)[1]
diff=''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='R2/prompts/system.md',tofile='A/prompts/system.md'))
(D/'CANDIDATE_A.diff').write_text(diff,encoding='utf8')
result=dict(status='CPU_VERIFIED_EXACT_SINGLE_BULLET',candidate_A_not_R3=True,only_changed_member=changed,unchanged_six_R2_rules=True,
    packages={n:{'zip_sha256':p['zip_sha256'],'members':{k:sha(v) for k,v in p['files'].items()}} for n,p in packages.items()},
    model='gemma-4-31b-it-qat-w4a16-ct',sampling_and_tools_and_budgets='Identical bytes in the three non-prompt members; genuine SDK CPU compile checked separately',real_model_requests=0)
(D/'PACKAGE_IDENTITY.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print(json.dumps(result))
