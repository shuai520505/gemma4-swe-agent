"""Prospective metadata selection and exact single-factor package; no model inference."""
import hashlib,io,json,os,re,sys,tarfile,zipfile
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
sys.path.insert(0,str(ROOT/'work/arrow-lib'))
import pyarrow.parquet as pq
sha=lambda b:hashlib.sha256(b).hexdigest()
DATA=Path('D:/kaggle/Gemma 4 Developer Agent Competition/private-evidence/egrd_v023/external-sources/test-00000-of-00001.parquet')
DATA_SHA='030cfd7f2a704c4c0226e7f104c725a3b41230b1d3517f9c915ad7ea5be3fa25'
REPOS={'sympy/sympy':(1,12),'sphinx-doc/sphinx':(7,1),'pylint-dev/pylint':(3,0),'pydata/xarray':(2022,3)}
SEED='R2A-v1|20261031|'
IDENT=re.compile(r'\b[A-Za-z0-9_.-]+__[A-Za-z0-9_.-]+-\d+\b')
SKIP={'.git','site-packages','node_modules','__pycache__','.venv','venv','sdk-env','snapshots','repositories','repos','official-inputs','external-sources','quality','candidates','attempt-01'}
def write(name,data):
    p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,indent=2)+'\n',encoding='utf8')
def main():
    assert sha(DATA.read_bytes())==DATA_SHA
    OUT.mkdir(exist_ok=True)
    amendment=dict(status='PREREGISTERED_BEFORE_NEW_ISSUE_INSPECTION',
        authorization='那就继续完成这个任务吧，可以在kaggle CIL上运行CPU和GPU进行实验',
        original_policy_and_R2_untouched=True,
        reason='Official Kaggle 129-row pool has no eligible holdout under its historical conservative exclusions; expand to already locally pinned public SWE-bench Verified, not hidden competition tasks.',
        source='SWE-bench/SWE-bench_Verified@78f471bf655a3137b2e8a75af1501690ec009ec3',source_sha256=DATA_SHA,
        original_official_task_count='UNKNOWN',
        endpoint='Unmodified pinned swegemma verify_task resolved on public SWE-bench tasks; NOT hidden competition Native, NOT canonical SWE-bench harness resolved.',
        repo_version_minimums={k:list(v) for k,v in REPOS.items()},
        infrastructure_basis='Four distinct pure-Python projects with pytest-compatible test paths and modern versions; avoids requiring a different interpreter/build ABI per arm. Compatibility is a declared restriction, not an issue-ease or repair-outcome filter.',
        selection='One lowest SHA256 of R2A-v1|20261031|repo.lower()|instance_id|base_commit|issue_sha256 per preregistered repository after identity exclusions. Repository ordering lexical; arm order from previously frozen seed/template.',
        replacements='NONE_AFTER_FREEZE: a selected infrastructure failure blocks the batch, no easier substitute or post-result selection.',
        sample_size=4,sessions=8,budget=dict(agent_seconds=480,charged_tools=28,max_turns=80,command_timeout_seconds=240),
        package_factor='Exactly the already frozen first CALL PLAN bullet replacement. No R2 suffix/config changes, A+B, R3 or model changes.',
        limitations=['Restricted modern-version pure-Python cohort; not representative of all hidden tasks.','Local identity audit cannot exclude model pretraining or unrecorded remote exposure.','Four pairs cannot establish noninferiority or Public Score 0.50.'],
        max_GPU_dispatches=1,maximum_notebook_seconds=18000,formal_submission_authorized=False)
    write('PROTOCOL_AMENDMENT.json',amendment)
    rows=pq.read_table(DATA,columns=['instance_id','repo','base_commit','problem_statement','version']).to_pylist()
    roots=[ROOT/'work/gemma-r12-01',ROOT/'work/gemma-pair-01/source',ROOT/'outputs',Path('D:/kaggle/Gemma 4 Developer Agent Competition/gemma4-egrd-v01'),Path('D:/kaggle/Gemma 4 Developer Agent Competition/gemma4-swe-agent')]
    excluded=set();evidence=[]
    for root in roots:
        for dp,dirs,files in os.walk(root):
            dirs[:]=[n for n in dirs if n not in SKIP]
            for n in files:
                p=Path(dp)/n
                if p.suffix not in {'.json','.md','.py'} or any(x in n.lower() for x in ('patch','secret','token')):continue
                if p.stat().st_size>4_000_000:continue
                raw=p.read_bytes()
                try:found=sorted(set(IDENT.findall(raw.decode('utf8'))))
                except UnicodeDecodeError:continue
                if found:excluded.update(found);evidence.append(dict(path=str(p),sha256=sha(raw),task_ids=found))
    excluded.update(['django__django-11964','pydata__xarray-6721','pytest-dev__pytest-5631','django__django-16333','pydata__xarray-3095'])
    aliases={(r['repo'].lower(),r['base_commit'],sha(r['problem_statement'].encode())) for r in rows if r['instance_id'] in excluded}
    pool=[]
    for r in rows:
        ver=tuple(int(x) for x in r['version'].split('.')[:2])
        issue_hash=sha(r['problem_statement'].encode());key=(r['repo'].lower(),r['base_commit'],issue_hash)
        if r['repo'] not in REPOS or ver<REPOS[r['repo']] or r['instance_id'] in excluded or key in aliases:continue
        rank=sha((SEED+r['repo'].lower()+'|'+r['instance_id']+'|'+r['base_commit']+'|'+issue_hash).encode())
        pool.append(dict(instance_id=r['instance_id'],repo=r['repo'],base_commit=r['base_commit'],issue_sha256=issue_hash,version=r['version'],rank=rank))
    chosen=[]
    for repo in sorted(REPOS):
        eligible=sorted([r for r in pool if r['repo']==repo],key=lambda r:(r['rank'],r['instance_id']))
        assert eligible,'NO_ELIGIBLE_TASK_FOR_'+repo
        chosen.append(eligible[0])
    write('EXPOSURE_AND_SELECTION.json',dict(excluded_ids=sorted(excluded),evidence=evidence,pool_identity_rows=pool,selected=chosen,source_sha256=DATA_SHA,no_reference_patch_column_read=True))
    # Freeze IDs before exposing original Issue bodies or loading trusted test specifications.
    write('TASK_IDENTITY_LOCK.json',dict(rows=chosen,replacements_allowed=False))
    issues=[]
    for c in chosen:
        r=next(r for r in rows if r['instance_id']==c['instance_id'])
        issues.append({k:r[k] for k in ('instance_id','repo','base_commit','problem_statement')})
    write('ISSUES.agent.json',issues)
    # Trusted evaluator-only fields. Reference repair/hints/eval_script columns are NEVER read.
    test_rows=pq.read_table(DATA,columns=['instance_id','test_patch','FAIL_TO_PASS','PASS_TO_PASS']).to_pylist()
    write('TRUSTED_TEST_SPEC.private.json',[r for r in test_rows if r['instance_id'] in {c['instance_id'] for c in chosen}])
    frozen=ROOT/'experiments/r2-final-audit/submission_r2_candidate.zip';raw=frozen.read_bytes()
    assert sha(raw)=='af918c1a65aeb211298f13a69b5b789ae6b086974922c80469df87d902eb98d5'
    spec=json.loads((ROOT/'experiments/r2-budget-optimization/candidate-a-design/CANDIDATE_A_POLICY_SPEC.json').read_bytes())
    with zipfile.ZipFile(io.BytesIO(raw)) as z:members={n:z.read(n) for n in z.namelist()}
    prompt=members['prompts/system.md'].decode();assert prompt.count(spec['old_exact'])==1
    replacement=prompt.replace(spec['old_exact'],spec['new_exact'],1).encode()
    assert sha(replacement)==spec['virtual_prompt_sha256']
    path=OUT/'candidates';path.mkdir(exist_ok=True)
    (path/'R2.zip').write_bytes(raw)
    with zipfile.ZipFile(path/'A.zip','w',zipfile.ZIP_DEFLATED) as z:
        for n,b in members.items():z.writestr(n,replacement if n=='prompts/system.md' else b)
    with zipfile.ZipFile(path/'A.zip') as z:
        assert [n for n,b in members.items() if z.read(n)!=b]==['prompts/system.md']
    arm_template=json.loads((ROOT/'experiments/r2-budget-optimization/candidate-a-design/holdout-preparation/SESSION_ORDER_TEMPLATE.json').read_bytes())
    sessions=[]
    for s in arm_template['sessions']:
        row=chosen[s['pair']-1]
        sessions.append(dict(index=s['index'],pair=s['pair'],task=row['instance_id'],candidate='R2' if s['arm']=='R2' else 'A'))
    write('EXECUTION_PLAN.json',dict(status='CPU_ADMISSION_PENDING',sessions=sessions,candidate_sha256={n:sha((path/(n+'.zip')).read_bytes()) for n in ('R2','A')},single_factor=True,one_GPU_dispatch_max=True))
    print(json.dumps(dict(selected=chosen,sessions=sessions,candidate_hashes={n:sha((path/(n+'.zip')).read_bytes()) for n in ('R2','A')})))
if __name__=='__main__':main()
