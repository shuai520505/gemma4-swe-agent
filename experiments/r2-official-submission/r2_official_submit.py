"""One explicit authorized frozen-R2 submission; read-only status thereafter."""
import argparse,hashlib,json,os,re,shutil,sys,zipfile
from datetime import datetime,timezone
from pathlib import Path
from kaggle.api.kaggle_api_extended import KaggleApi
from kagglesdk.competitions.types.competition_api_service import ApiGetCompetitionRequest,ApiGetSubmissionLimitsRequest,ApiGetSubmissionRequest

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent/'attempt-01'
SOURCE=ROOT/'experiments/r2-final-audit/submission_r2_candidate.zip'
EXPECTED='af918c1a65aeb211298f13a69b5b789ae6b086974922c80469df87d902eb98d5'
COMP='gemma-4-developer-agent'
MESSAGE='R2 frozen af918c1a65ae; exact prompt-only baseline delta; audit e84aa2b'
sha=lambda b:hashlib.sha256(b).hexdigest()
now=lambda:datetime.now(timezone.utc).isoformat()

def save(name,data):
    OUT.mkdir(exist_ok=True,parents=True)
    (OUT/name).write_text(json.dumps(data,indent=2,default=str)+'\n',encoding='utf8')

def safe_error(exc):
    text=str(exc)
    text=re.sub(r'https?://\S+','[URL REDACTED]',text)
    text=re.sub(r'(?i)(token|password|authorization|api[_-]?key)\s*[:=]\s*\S+',r'\1=[REDACTED]',text)
    return dict(error_type=type(exc).__name__,message=text[:1800])

def api():
    client=KaggleApi();client.authenticate();return client

def submission(s):
    row={k:getattr(s,k,None) for k in ('ref','date','description','file_name','total_bytes','public_score','error_description','url')}|{'status':getattr(getattr(s,'status',None),'name',None)}
    if row['public_score']=='':row['public_score']=None
    if not row['total_bytes']:row['total_bytes']=None
    return row

def package():
    assert sha(SOURCE.read_bytes())==EXPECTED
    manifest=json.loads((ROOT/'experiments/r2-final-audit/R2_SUBMISSION_MANIFEST.json').read_bytes())
    assert manifest['zip_sha256']==EXPECTED and manifest['official_compiler']['status']=='PASS'
    with zipfile.ZipFile(SOURCE) as z:
        assert z.testzip() is None and set(z.namelist())==set(manifest['files'])
        for n,info in manifest['files'].items():assert sha(z.read(n))==info['sha256'],n
    OUT.mkdir(exist_ok=True,parents=True)
    dest=OUT/'submission.zip'
    if dest.exists():assert sha(dest.read_bytes())==EXPECTED
    else:shutil.copyfile(SOURCE,dest)
    assert sha(dest.read_bytes())==EXPECTED
    return dest

def preflight():
    dest=package();a=api()
    with a.build_kaggle_client() as k:
        q=ApiGetCompetitionRequest();q.competition_name=COMP
        c=k.competitions.competition_api_client.get_competition(q)
        q2=ApiGetSubmissionLimitsRequest();q2.competition_name=COMP
        limit=k.competitions.competition_api_client.get_submission_limits(q2)
    rows=[submission(s) for s in (a.competition_submissions(COMP,page_size=200) or []) if s is not None]
    duplicate=[s for s in rows if EXPECTED in (s['description'] or '') or 'af918c1a65ae' in (s['description'] or '')]
    metadata={f:getattr(c,f,None) for f in ('ref','title','deadline','user_has_entered','max_daily_submissions','is_kernels_submissions_only','submissions_disabled')}
    allowance={f:getattr(limit,f,None) for f in ('num_today','num_total','num_allowed_now','limited_by_total')}
    blockers=[]
    if c.submissions_disabled:blockers.append('SUBMISSIONS_DISABLED')
    if c.is_kernels_submissions_only:blockers.append('DIRECT_ZIP_SUBMISSION_NOT_ALLOWED')
    if not c.user_has_entered:blockers.append('NOT_ENTERED')
    if limit.num_allowed_now<1:blockers.append('NO_SUBMISSION_ALLOWANCE')
    deadline=c.deadline
    if deadline and deadline.replace(tzinfo=deadline.tzinfo or timezone.utc)<datetime.now(timezone.utc):blockers.append('DEADLINE_PASSED')
    if duplicate:blockers.append('EXACT_R2_ALREADY_LISTED_NO_DUPLICATE_SUBMISSION')
    if (OUT/'SUBMISSION_ATTEMPT_LOCK.json').exists():blockers.append('LOCAL_SUBMISSION_ALREADY_ATTEMPTED')
    result=dict(checked_at_utc=now(),competition=metadata,limits=allowance,authenticated=True,package_path=str(dest),zip_sha256=EXPECTED,zip_bytes=dest.stat().st_size,historical_audit_gate='R2_BLOCKED_BY_BUDGET',budget_unknowns_retained=True,
        current_user_authorization='我觉得我们可以先把目前最好的先打包提交一下',
        scope='One exact frozen R2 formal competition submission; no prompt/config changes, new Notebook, R3 or local model inference.',
        latest_submissions=rows,duplicates=duplicate,blockers=blockers,status='PASS' if not blockers else 'BLOCKED')
    save('PREFLIGHT.json',result)
    print(json.dumps({k:result[k] for k in ('status','competition','limits','zip_sha256','blockers')},default=str))
    return not blockers

def submit():
    if not preflight():raise SystemExit('PRECHECK_BLOCKED_NO_SUBMISSION')
    dest=package();a=api()
    # Exclusive persistent marker before the sole mutating call. An uncertain response never authorizes retry.
    marker=dict(at_utc=now(),status='ATTEMPT_STARTED',zip_sha256=EXPECTED,message=MESSAGE,competition=COMP,explicit_submission_calls_allowed=1)
    with (OUT/'SUBMISSION_ATTEMPT_LOCK.json').open('x',encoding='utf8') as f:json.dump(marker,f,indent=2)
    try:
        r=a.competition_submit(str(dest),MESSAGE,COMP,quiet=True,sandbox=False)
        receipt=dict(at_utc=now(),submission_id=r.ref,message=r.message,zip_sha256=EXPECTED,competition=COMP,formal_submission=True,explicit_mutation_calls=1,status='ACCEPTED' if r.ref else 'UNCERTAIN_DO_NOT_RESUBMIT')
        save('SUBMISSION_RECEIPT.json',receipt)
        print(json.dumps(receipt))
    except Exception as exc:
        receipt=dict(at_utc=now(),status='ERROR_OR_UNCERTAIN_DO_NOT_RESUBMIT',explicit_mutation_calls=1,zip_sha256=EXPECTED,**safe_error(exc))
        save('SUBMISSION_RECEIPT.json',receipt);print(json.dumps(receipt));raise SystemExit(2)

def status():
    receipt=json.loads((OUT/'SUBMISSION_RECEIPT.json').read_bytes());sid=receipt.get('submission_id')
    if not sid:raise SystemExit('NO_CONFIRMED_ID_READ_LIST_TO_RECONCILE_DO_NOT_RESUBMIT')
    a=api()
    with a.build_kaggle_client() as k:
        q=ApiGetSubmissionRequest();q.ref=sid
        row=k.competitions.competition_api_client.get_submission(q)
        q2=ApiGetSubmissionLimitsRequest();q2.competition_name=COMP
        limit=k.competitions.competition_api_client.get_submission_limits(q2)
    result=dict(checked_at_utc=now(),submission=submission(row),limits={f:getattr(limit,f,None) for f in ('num_today','num_total','num_allowed_now','limited_by_total')},zip_sha256=EXPECTED,read_only=True)
    save('LATEST_STATUS.json',result)
    with (OUT/'STATUS_HISTORY.jsonl').open('a',encoding='utf8') as f:f.write(json.dumps(result,default=str)+'\n')
    print(json.dumps(result,default=str))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['preflight','submit','status']);args=p.parse_args()
    try:globals()[args.mode]()
    except Exception as exc:
        save('LOCAL_ERROR.json',dict(at_utc=now(),**safe_error(exc)));print(json.dumps(safe_error(exc)));raise SystemExit(1)
