"""Read official status only; this module never submits or retries creation."""
from datetime import datetime,timezone
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def main():
    import requests
    original=requests.Session.send
    def send(self,request,**kwargs):
        kwargs.setdefault('timeout',30)
        assert 'CreateCodeSubmission' not in request.url
        return original(self,request,**kwargs)
    requests.Session.send=send
    from kaggle import api
    rows=[s.to_dict(ignore_defaults=False) for s in api.competition_submissions('gemma-4-developer-agent')]
    stamp=datetime.now(timezone.utc).isoformat()
    evidence=HERE/'submission_evidence/submission_status_history.jsonl'
    with evidence.open('a',encoding='utf-8') as f:f.write(json.dumps(dict(observed_at_utc=stamp,submissions=rows),default=str)+'\n')
    record_path=HERE/'OFFICIAL_SUBMISSION_RECORD.json'
    record=json.loads(record_path.read_text()) if record_path.exists() else {}
    matches=[r for r in rows if (record.get('submission_id') and r['ref']==record['submission_id'])
        or 'S2 EGV AgentTool T500 first official score'==r.get('description')]
    assert len(matches)<=1,'Ambiguous submissions; manual audit required, never resubmit.'
    if matches:
        r=matches[0]
        record.update(submission_id=r['ref'],status=r['status'],public_score=r.get('publicScore') or None,
            private_score=r.get('privateScore') or None,official_error=r.get('errorDescription'),last_observed_at_utc=stamp,official_status_record=r)
        record_path.write_bytes((json.dumps(record,indent=2,default=str)+'\n').encode())
    print(json.dumps(record if matches else dict(status='NO_MATCH_IN_OFFICIAL_LIST',submissions=len(rows)),indent=2,default=str))


if __name__=='__main__':main()
