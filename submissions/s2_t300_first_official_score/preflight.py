"""Read-only competition/account/limit/duplicate checks for frozen S2-T300."""
import json
from datetime import datetime,timezone
from pathlib import Path
HERE=Path(__file__).resolve().parent


def inspect():
 import requests
 original=requests.Session.send
 def send(self,r,**kw):kw.setdefault('timeout',30);return original(self,r,**kw)
 requests.Session.send=send
 from kaggle import api
 from kagglesdk.competitions.types.competition_api_service import ApiGetSubmissionLimitsRequest,ApiGetCompetitionRequest
 with api.build_kaggle_client() as k:
  c=k.competitions.competition_api_client
  r=ApiGetSubmissionLimitsRequest();r.competition_name='gemma-4-developer-agent';limits=c.get_submission_limits(r).to_dict(ignore_defaults=False)
  r=ApiGetCompetitionRequest();r.competition_name='gemma-4-developer-agent';comp=c.get_competition(r)
  eligibility=dict(user_has_entered=comp.user_has_entered,submissions_disabled=comp.submissions_disabled,deadline=comp.deadline,max_daily_submissions=comp.max_daily_submissions)
 rows=[s.to_dict(ignore_defaults=False) for s in api.competition_submissions('gemma-4-developer-agent')]
 data=dict(observed_at_utc=datetime.now(timezone.utc).isoformat(),limits=limits,eligibility=eligibility,submissions=rows,
  matching_t300=[r for r in rows if 'S2 EGV AgentTool T300' in (r.get('description') or '')])
 out=HERE/'evidence';out.mkdir(exist_ok=True)
 stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
 (out/('preflight_'+stamp+'.json')).write_bytes((json.dumps(data,indent=2,default=str)+'\n').encode())
 (HERE/'LATEST_PREFLIGHT.json').write_bytes((json.dumps(data,indent=2,default=str)+'\n').encode())
 return data

if __name__=='__main__':
 d=inspect();print(json.dumps(dict(limits=d['limits'],existing_t300=len(d['matching_t300']),submission_states=[dict(id=r['ref'],status=r['status'],score=r.get('publicScore')) for r in d['submissions']]),indent=2))
