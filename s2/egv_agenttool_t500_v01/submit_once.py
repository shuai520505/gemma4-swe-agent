"""One authorized official request, after gates; uncertain response never retried."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import zipfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
SLUG='wudangdexiaodoashi/gemma4-s2-t500-first-official-score'
DESCRIPTION='S2 EGV AgentTool T500 first official score'
COMPETITION='gemma-4-developer-agent'


def emit(path,data):
    path.write_bytes((json.dumps(data,indent=2,default=str)+'\n').encode())


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    import requests
    from urllib3.util.retry import Retry
    from kaggle import api
    from kagglesdk.competitions.types.competition_api_service import ApiGetCompetitionRequest,ApiGetSubmissionLimitsRequest
    record=HERE/'OFFICIAL_SUBMISSION_RECORD.json'
    intent=HERE/'submission_evidence/SUBMISSION_INTENT.json'
    assert not intent.exists(),'Already attempted; query official submissions, never resend.'
    acceptance=json.loads((HERE/'CPU_FEASIBILITY.json').read_text())
    assert acceptance['passed'] and acceptance['original115_passed'] and acceptance['actual_deadline_seconds']==500
    for n,h in acceptance['tested_runtime_hashes'].items():assert sha(ROOT/n)==h,n
    candidate=json.loads((HERE/'candidate.json').read_text());assert sha(HERE/'submission.zip')==candidate['zip_sha256']
    base=json.loads((HERE/'BASE_INTEGRITY.json').read_text())
    for n,h in base['files'].items():assert sha(ROOT/n)==h,n
    package=HERE/'submission_evidence/package_v1'
    saved=json.loads((package/'saved_version_record.json').read_text())
    assert saved['status']=='COMPLETE' and saved['version']==1 and saved['slug']==SLUG
    assert sha(package/'submission.zip')==candidate['zip_sha256']
    with zipfile.ZipFile(package/'submission.zip') as z:assert z.testzip() is None and len(z.namelist())==5 and 'agent.yaml' in z.namelist()
    risk=json.loads((HERE/'GLOBAL_BUDGET_MODEL.json').read_text())
    # Risk remains disclosed/uncalibrated; never convert assumed scenario
    # frequencies into real population probabilities or a guarantee of fit.
    decision=json.loads((HERE/'SUBMISSION_GATE_DECISION.json').read_text())
    assert decision['official_submission_go'] and decision['budget_risk_disclosed']
    assert not decision['supported_high_probability_large_task_loss']
    now=datetime.now(timezone.utc).isoformat();pre=dict(observed_at_utc=now)
    with api.build_kaggle_client() as k:
        c=k.competitions.competition_api_client
        req=ApiGetCompetitionRequest();req.competition_name=COMPETITION;competition=c.get_competition(req)
        req=ApiGetSubmissionLimitsRequest();req.competition_name=COMPETITION;limits=c.get_submission_limits(req)
        pre.update(competition=competition.to_dict(ignore_defaults=False),limits=limits.to_dict(ignore_defaults=False))
        assert competition.user_has_entered and not competition.submissions_disabled
        deadline=competition.deadline
        if deadline.tzinfo is None:deadline=deadline.replace(tzinfo=timezone.utc)
        assert deadline>datetime.now(timezone.utc)
        assert limits.num_allowed_now>=1
    submissions=api.competition_submissions(COMPETITION)
    pre['submissions']=[s.to_dict(ignore_defaults=False) for s in submissions]
    assert not any('t500' in json.dumps(s).lower() for s in pre['submissions']),'Duplicate or uncertain T500 already accepted.'
    emit(HERE/'submission_evidence/preflight_before_submit.json',pre)
    original=requests.Session.send
    def send(session,request,**kwargs):
        kwargs.setdefault('timeout',30)
        if 'CreateCodeSubmission' in request.url:
            session.get_adapter(request.url).max_retries=Retry(total=0,connect=0,read=0,redirect=0,status=0)
            with intent.open('x',encoding='utf-8') as f:
                json.dump(dict(at_utc=datetime.now(timezone.utc).isoformat(),slug=SLUG,version=1,
                    candidate_zip_sha256=candidate['zip_sha256'],scope='Persistent one-request latch; no automatic retries even if outcome is uncertain.'),f,indent=2)
            emit(record,dict(candidate=candidate['name'],notebook_slug=SLUG,notebook_version=1,
                zip_sha256=candidate['zip_sha256'],status='REQUEST_SENT_OUTCOME_UNKNOWN',submission_id=None,
                public_score=None,request_attempts=1,submitted_at_utc=datetime.now(timezone.utc).isoformat()))
        response=original(session,request,**kwargs)
        if 'CreateCodeSubmission' in request.url:
            emit(HERE/'submission_evidence/create_code_submission_HTTP.json',dict(
                status_code=response.status_code,body=response.text,received_at_utc=datetime.now(timezone.utc).isoformat()))
        return response
    requests.Session.send=send
    try:
        response=api.competition_submit_code(file_name='submission.zip',message=DESCRIPTION,competition=COMPETITION,
            kernel=SLUG,kernel_version=1,quiet=True)
        raw=response.to_dict(ignore_defaults=False)
        emit(HERE/'submission_evidence/create_code_submission_response.json',raw)
        prior=json.loads(record.read_text());prior.update(status='ACCEPTED_QUERY_STATUS',submission_id=response.ref or None,official_response=raw)
        emit(record,prior);print(json.dumps(raw,indent=2,default=str))
    except BaseException as exc:
        if record.exists():
            prior=json.loads(record.read_text());prior['request_exception']=repr(exc);emit(record,prior)
        raise
    finally:requests.Session.send=original


if __name__=='__main__':main()
