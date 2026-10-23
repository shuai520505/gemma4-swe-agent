"""Read actual historical private HTTP events, publish statistics without messages."""
import json,math,zipfile
from pathlib import Path
from collections import Counter
from .common import HERE,ROOT,write,sha
ARCHIVES=[
 ('GPU03',ROOT.parent/'private-evidence/u_re_real_gemma_abba03/read-06/evidence_confirmed/output/u_re_actionfirst_abba03.zip','72030f1833ee6a8588087836bf281ae3aafae4c5a327b4f1d5651482aed7bea6'),
 ('V02B_BATCH1',ROOT.parent/'private-evidence/u_re_v02b_gemma_batch01/read-04/evidence_confirmed/output/v02b-gemma-batch01.zip','6ecb9bfceb0b230ea3f4a2281b219d1e94c1ff2e50d4b0960b8701b4e7af2e45')]
def distribution(values):
    v=sorted(values)
    def percentile(p):
        if not v:return None
        x=(len(v)-1)*p;i=math.floor(x);return v[i]+(v[min(i+1,len(v)-1)]-v[i])*(x-i)
    return dict(n=len(v),P50=percentile(.5),P90=percentile(.9),P95=percentile(.95),P99=percentile(.99),maximum=max(v,default=None),mean=sum(v)/len(v) if v else None)
def analyze():
    sessions=[];allrows=[];sources=[]
    for cohort,path,expected in ARCHIVES:
        assert sha(path.read_bytes())==expected
        sources.append(dict(cohort=cohort,archive_sha256=expected,bytes=path.stat().st_size))
        with zipfile.ZipFile(path) as z:
            assert z.testzip() is None
            for wire in sorted(n for n in z.namelist() if n.endswith('agent/http_wire.jsonl')):
                root=wire.removesuffix('agent/http_wire.jsonl');runlabel=root.split('/')[-2];_,task,arm=runlabel.split('-',2)
                events=[json.loads(x) for x in z.read(wire).splitlines()];reqs={e['request_id']:e for e in events if e['kind']=='http_request'}
                rows=[];last=None
                for response in [e for e in events if e['kind']=='http_response']:
                    request=reqs[response['request_id']];b=request['body'];v=response['body'];u=v.get('usage',{});choice=v['choices'][0];msg=choice['message'];cap=b.get('max_completion_tokens',b.get('max_tokens'))
                    assert cap==16384 and b['thinking_token_budget']==4096 and b['seed']==17
                    messages=b['messages'];tools=[m for m in messages if m.get('role')=='tool']
                    row=dict(cohort=cohort,task=task,candidate='NoEGV' if arm=='A' else 'Action-First',request=len(rows)+1,prompt_tokens=u.get('prompt_tokens'),completion_tokens=u.get('completion_tokens'),total_tokens=u.get('total_tokens'),input_growth=None if last is None else u.get('prompt_tokens')-last,finish_reason=choice.get('finish_reason'),stop_reason=choice.get('stop_reason'),output_cap=cap,thinking_budget=b['thinking_token_budget'],reasoning_present=bool(msg.get('reasoning')),reasoning_tokens=None,response_class='tool_call' if msg.get('tool_calls') else 'text',tool_calls=len(msg.get('tool_calls') or []),history_messages=len(messages),history_content_characters=sum(len(json.dumps(m,ensure_ascii=False)) for m in messages),tool_response_messages=len(tools),tool_response_characters=sum(len(json.dumps(m,ensure_ascii=False)) for m in tools),tool_token_increment=None,HTTP_status=response['status'],truncated=choice.get('finish_reason')=='length')
                    last=u.get('prompt_tokens');rows.append(row);allrows.append(row)
                guards=[]
                for suffix in ('events.jsonl','agent/events.jsonl'):
                    if root+suffix in z.namelist():guards += [json.loads(x) for x in z.read(root+suffix).splitlines() if json.loads(x).get('kind')=='context_admission']
                cfg=json.loads(z.read(root+'runtime_config.json'))
                assert cfg['generation']['max_output_tokens']==cfg['budget']['output_tokens']==16384
                sessions.append(dict(cohort=cohort,task=task,candidate=rows[0]['candidate'],wire_sha256=sha(z.read(wire)),runtime_config_sha256=sha(z.read(root+'runtime_config.json')),requests=rows,context_admissions=[{k:e.get(k) for k in ('input_tokens','output_reserved','decision','total_reserved')} for e in guards]))
    groups={}
    for field in ('cohort','task','candidate','response_class'):
        groups[field]={v:distribution([r['completion_tokens'] for r in allrows if r[field]==v]) for v in sorted({r[field] for r in allrows})}
    write(HERE/'OFFLINE_OUTPUT_DISTRIBUTION.json',dict(sources=sources,overall=distribution([r['completion_tokens'] for r in allrows]),groups=groups,finish_reasons=dict(Counter(r['finish_reason'] for r in allrows)),truncated_requests=sum(r['truncated'] for r in allrows),sessions=sessions,thinking='4096 passed in actual HTTP; reasoning content observed separately, completion usage has no independent reasoning_tokens. Exact thinking-token allocation UNKNOWN. Completion usage is server reported; do not infer reasoning zero.',growth='Input differences are actual full-chat token differences, not causal per-tool Token attribution. Tool/history character counts are not token estimates. Exact per-tool token contribution UNKNOWN without actual tokenizer replay.'))
    policies=[]
    for cap in (16384,8192,4096):
        sessionrows=[]
        for s in sessions:
            admissions=s['context_admissions'];rejects=[e for e in admissions if e['decision']=='reject']
            sessionrows.append(dict(cohort=s['cohort'],task=s['task'],candidate=s['candidate'],observed_requests_admitted=sum(r['prompt_tokens']+cap+1024<=32768 for r in s['requests']),observed_requests=len(s['requests']),historical_completions_exceed_cap=sum(r['completion_tokens']>cap for r in s['requests']),old_rejected_requests=[dict(input_tokens=e['input_tokens'],new_guard_allows=e['input_tokens']+cap+1024<=32768) for e in rejects],additional_request_opportunity=any(e['input_tokens']+cap+1024<=32768 for e in rejects)))
        policies.append(dict(max_output=cap,theoretical_input_cap=32768-cap-1024,released_input=16384-cap,sessions=sessionrows))
    write(HERE/'CONTEXT_SHADOW_ANALYSIS.json',dict(policies=policies,limitations='Observed requests only; changed cap can change subsequent generation and trajectory. Additional opportunity is not a generated request or repair outcome. P2=4096 offline only; existing Config refuses thinking4096>=output4096 and no P2 runtime is proposed.'))
    print(json.dumps(dict(distribution=distribution([r['completion_tokens'] for r in allrows]),requests=len(allrows),finish=dict(Counter(r['finish_reason'] for r in allrows)))))
if __name__=='__main__':analyze()
