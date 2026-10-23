"""Read-only official score snapshots. Never submits or saves a Notebook."""
from datetime import datetime,timezone
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
COMP='gemma-4-developer-agent'
def main():
    from kaggle import api
    assert api.get_config_value('username')=='wudangdexiaodoashi'
    rows=api.competition_submissions(COMP)
    safe=[]
    for r in rows:
        d=r.to_dict(ignore_defaults=False)
        safe.append({k:d.get(k) for k in ('ref','status','date','publicScore','errorDescription','description')})
    folder=HERE/'scoring/status';folder.mkdir(parents=True,exist_ok=True)
    now=datetime.now(timezone.utc)
    with (folder/(now.strftime('%Y%m%dT%H%M%S%fZ')+'.json')).open('x',encoding='utf-8') as f:
        json.dump(dict(queried_utc=now.isoformat(),competition=COMP,submissions=safe,SaveKernel=0,CreateCodeSubmission=0),f,indent=2,default=str)
    receipt=HERE/'scoring/RESULT.json'
    target=json.loads(receipt.read_bytes()).get('submission_id') if receipt.exists() else None
    chosen=[x for x in safe if str(x['ref'])==str(target)] if target else safe
    print(json.dumps(chosen,default=str))
if __name__=='__main__':main()
