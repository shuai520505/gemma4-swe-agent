"""Prepare Issue/source/tool-only review before opening native Agent outcomes.

No official_result, JUnit, verifier directory or final patch is read here.
Private contents never enter public summaries or the Agent runtime.
"""
import hashlib,json,re,zipfile
from pathlib import Path
from .read_preflight import HERE,PRIVATE,save

def sha(raw):return hashlib.sha256(raw).hexdigest()

def prepare(batch,archive):
    archive=Path(archive).resolve();out=PRIVATE/f'batch{batch:02d}/blinded-review';out.mkdir(parents=True,exist_ok=False)
    index=[]
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        members=z.namelist()
        for name in sorted(n for n in members if re.search(r'(?:^|/)runs/[^/]+/agent/adk_events\.jsonl$',n)):
            pre=name.removesuffix('agent/adk_events.jsonl');label=pre.rstrip('/').rsplit('/',1)[-1]
            raw=z.read(name);events=[json.loads(x) for x in raw.splitlines() if x.strip()]
            wire=[json.loads(x) for x in z.read(pre+'agent/http_wire.jsonl').splitlines() if x.strip()]
            requests=[x for x in wire if x.get('kind')=='http_request']
            issue_messages=[m for m in (requests[0].get('body',{}).get('messages',[]) if requests else []) if m.get('role')=='user']
            calls=[];responses={}
            for i,row in enumerate(events):
                for part in row.get('event',{}).get('content',{}).get('parts',[]):
                    if part.get('function_call'):calls.append(dict(part['function_call'],event_index=i,monotonic=row.get('recorded_monotonic')))
                    if part.get('function_response'):
                        r=part['function_response'];responses[r.get('id')]=dict(r,event_index=i,monotonic=row.get('recorded_monotonic'))
            actions=[]
            for call in calls:
                response=responses.get(call.get('id'))
                actions.append(dict(call=call,response=response))
            changes=[json.loads(x) for x in z.read(pre+'agent/events.jsonl').splitlines() if x.strip()]
            changes=[r for r in changes if r.get('kind')=='source_boundary_observation']
            pack=dict(session=label,issue_messages=issue_messages,actions=actions,source_boundary_observations=changes,
                      native_outcome_hidden=True,archive_sha256=sha(archive.read_bytes()),trace_member=name,trace_sha256=sha(raw))
            save(out/(label+'.json'),pack)
            checks=[c['event_index'] for c in calls if c.get('name')=='run_skill_script' or (c.get('name')=='run_command' and re.search(r'\b(?:pytest|unittest|python\d*(?:\.\d+)?|assert)\b',str(c.get('args',{}).get('command',''))))]
            index.append(dict(session=label,trace_sha256=sha(raw),tool_calls=len(calls),check_event_candidates=checks,raw_review_private=True))
    save(HERE/f'BLINDED_REVIEW_BATCH_{batch:02d}.json',dict(batch=batch,sessions=index,native_outcomes_read=False,
          review_lock_required_before_native_analysis=True,archive_sha256=sha(archive.read_bytes())))
    print(json.dumps(dict(batch=batch,blinded_sessions=len(index),sessions=index)))

if __name__=='__main__':
    import sys
    prepare(int(sys.argv[1]),sys.argv[2])
