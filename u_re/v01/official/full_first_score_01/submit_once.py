"""Exactly one human-authorized CreateCodeSubmission; uncertain response never retries."""
from datetime import datetime,timezone
import hashlib,json,os,subprocess
from pathlib import Path
from urllib.parse import urlsplit
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
COMP='gemma-4-developer-agent';REF='wudangdexiaodoashi/u-re-full-v01-first-official-score'
MESSAGE='U-RE Full V0.1 single agent EGV 300s 60tools first official score'
def write(name,value):
    path=HERE/'scoring'/name;path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as f:json.dump(value,f,indent=2,default=str);f.flush();os.fsync(f.fileno())
def main():
    if (HERE/'HUMAN_SUBMISSION_CONFIRMATION.json').exists():raise RuntimeError('Human already submitted this candidate; never dispatch a duplicate')
    if (HERE/'scoring/dispatch.claim').exists():raise RuntimeError('Existing scoring claim; read-only reconciliation only')
    p=json.loads((HERE/'PACKAGING_VERIFIED.json').read_text(encoding='utf-8'));assert p['verified'] and p['version']==1 and p['ref']==REF
    raw=(ROOT/'u_re/v01/submission_full.zip').read_bytes();assert hashlib.sha256(raw).hexdigest()==p['ZIP_sha256']
    assert json.loads((ROOT/'u_re/v01/results/cpu02/validation/compiler_empty_state_gate.json').read_text(encoding='utf-8'))['full']['passed']
    core=ROOT/'u_re/v01/experiments/gemma_smoke_01/recovery_01/cpu02/derived_results/official_acceptance/CPU_INTERFACE_GATE.json'
    assert json.loads(core.read_text(encoding='utf-8'))['passed']
    from kaggle import api
    assert api.get_config_value('username')=='wudangdexiaodoashi'
    from kagglesdk.competitions.types.competition_api_service import ApiGetCompetitionRequest,ApiGetSubmissionLimitsRequest
    from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelRequest
    with api.build_kaggle_client() as client:
        q=ApiGetCompetitionRequest();q.competition_name=COMP;c=client.competitions.competition_api_client.get_competition(q)
        assert c.user_has_entered and not c.submissions_disabled
        q=ApiGetSubmissionLimitsRequest();q.competition_name=COMP;limits=client.competitions.competition_api_client.get_submission_limits(q)
        assert limits.num_allowed_now>=1
        q=ApiGetKernelRequest();q.user_name=REF.split('/')[0];q.kernel_slug=REF.split('/')[1]
        k=client.kernels.kernels_api_client.get_kernel(q).metadata
        assert k.id==140121936 and k.current_version_number==1 and k.ref==REF
    rows=api.competition_submissions(COMP)
    assert not any('U-RE' in (r.description or '') for r in rows),'Potential duplicate U-RE scoring attempt'
    write('PREFLIGHT.json',dict(utc=datetime.now(timezone.utc).isoformat(),account_confirmed=True,user_has_entered=True,submissions_disabled=False,limits=limits.to_dict(ignore_defaults=False),Notebook_id=k.id,version=1,ref=REF,ZIP_sha256=p['ZIP_sha256'],candidate='U-RE-Full',research_isolation_blocked=True,official_sandbox_used=True,budget_risk_document='SUBMISSION_DECISION.md',human_authorization='继续完成任务，然后给我把现在这个框架提交，让我这个框架有分数',max_requests=1))
    original=requests.Session.send;count=0
    def send(session,request,**kwargs):
        nonlocal count
        u=urlsplit(request.url)
        assert request.method=='POST' and u.hostname=='api.kaggle.com' and u.path=='/v1/competitions.CompetitionApiService/CreateCodeSubmission' and not u.query
        assert count==0,'Duplicate scoring transport blocked'
        b=json.loads(request.body)
        assert b['competitionName']==COMP and b['kernelOwner']=='wudangdexiaodoashi' and b['kernelSlug']==REF.split('/')[1] and b['kernelVersion']==1 and b['fileName']=='submission.zip'
        session.mount('https://api.kaggle.com/',HTTPAdapter(max_retries=Retry(total=0,connect=0,read=0,status=0,redirect=0,other=0)))
        kwargs.update(timeout=60,allow_redirects=False)
        write('dispatch.claim',dict(utc=datetime.now(timezone.utc).isoformat(),operation='CreateCodeSubmission',ref=REF,version=1,candidate_sha256=p['ZIP_sha256'],source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()))
        count=1
        r=original(session,request,**kwargs)
        write('HTTP_METADATA.json',dict(utc=datetime.now(timezone.utc).isoformat(),HTTP_status=r.status_code,content_type=r.headers.get('Content-Type','').split(';')[0],bytes=len(r.content)))
        try:
            j=r.json();safe={}
            if type(j.get('ref')) is int:safe['submission_id']=j['ref']
            safe['JSON_parsed']=True
            write('HTTP_RECEIPT.json',safe)
        except ValueError:write('HTTP_RECEIPT.json',dict(JSON_parsed=False))
        return r
    requests.Session.send=send
    try:
        r=api.competition_submit_code('submission.zip',MESSAGE,COMP,REF,1,quiet=True)
        write('RESULT.json',dict(state='ACCEPTED' if r.ref else 'UNKNOWN_STOP',submission_id=r.ref or None,request_count=count,score=None))
        print(json.dumps(dict(submission_id=r.ref,requests=count)))
    except BaseException as exc:
        write('RESULT.json',dict(state='UNKNOWN_STOP' if count else 'LOCAL_BLOCKED_NO_REQUEST',exception_class=type(exc).__name__,request_count=count,score=None))
        print(json.dumps(dict(state='UNKNOWN_STOP' if count else 'LOCAL_BLOCKED_NO_REQUEST',exception_class=type(exc).__name__,requests=count)))
    finally:requests.Session.send=original
if __name__=='__main__':main()
