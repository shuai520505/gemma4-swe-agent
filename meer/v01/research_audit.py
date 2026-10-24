"""Read historical tools/identity only; never inspect reference or evaluator patches."""
import hashlib
import json
from pathlib import Path
import re
import zipfile
from .build import HERE,ROOT,sha


def run():
    known=json.loads((ROOT/'u_re/v04/experiments/evidence_guided_repair_01/RAW_ARCHIVES.json').read_bytes())
    reports=[]
    for archive in known['historical_traces']:
        raw=Path(archive['path']).read_bytes();assert sha(raw)==archive['sha256']
        with zipfile.ZipFile(__import__('io').BytesIO(raw)) as z:
            assert z.testzip() is None
            for name in sorted(n for n in z.namelist() if n.endswith('agent/adk_events.jsonl')):
                # Only normal Agent-visible tool calls/results. No verifier test
                # contents, reference/gold patch, or actual successful patch read.
                rows=[json.loads(x) for x in z.read(name).splitlines()]
                calls=[];responses={}
                for event in rows:
                    for part in event.get('event',{}).get('content',{}).get('parts',[]):
                        if part.get('function_call'):calls.append(part['function_call'])
                        if part.get('function_response'):
                            r=part['function_response'];responses[r['id']]=r
                seen=set();repeat=0;broad=0;assertion_mentions=0
                for c in calls:
                    args=c.get('args') or {};command=args.get('command','')
                    r=(responses.get(c.get('id')) or {}).get('response')
                    if c['name']=='run_command' and re.search(r'(^|[;&|\s])(rg|grep|find)\s',command):
                        key=(sha(command.encode()),sha(json.dumps(r,sort_keys=True).encode()))
                        repeat+=key in seen;seen.add(key)
                    broad+=bool(c['name']=='run_command' and re.search(r'(?:^|&&\s*|;\s*)(?:python3? -m )?pytest\s*$',command))
                    assertion_mentions+=bool('assert ' in args.get('content',args.get('new_string',command)))
                reports.append(dict(cohort=archive['cohort'],session=name.split('/')[-3],tool_calls=len(calls),
                    repeated_exact_search_response_pairs=repeat,unscoped_pytest_commands=broad,
                    actions_containing_assert_syntax=assertion_mentions,
                    assert_syntax_is_not_execution_proof=True,semantic_information_gain=None,
                    raw_ADK_events_sha256=sha(z.read(name))))
    result=dict(archives=[{k:a[k] for k in ('cohort','sha256','bytes')} for a in known['historical_traces']],
        sessions=reports,total_sessions=len(reports),total_tool_calls=sum(r['tool_calls'] for r in reports),
        limitation='Repeated query/result is not automatically useless: external state and task purpose may differ. Assertion text does not prove execution.',
        reference_patch_read=False,evaluator_test_content_read=False)
    assert result['total_sessions']==12 and result['total_tool_calls']==315
    (HERE/'HISTORICAL_TRACE_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    base=ROOT.parent/'gemma4-swe-agent/artifacts/harness-v2/official-wheels'
    sources={}
    wanted={'adk_submission-0.2.13-py3-none-any.whl':['adk_submission/compiler.py','adk_submission/schema.py','adk_submission/resolvers/tools.py','adk_submission/resolvers/callbacks.py'],
            'google_adk-1.36.1-py3-none-any.whl':['google/adk/tools/skill_toolset.py'],
            'adk_eval_core-0.1.0-py3-none-any.whl':['adk_eval_core/sandbox/base.py'],
            'swegemma-0.2.11-py3-none-any.whl':['swegemma/harness/agent_runner.py','swegemma/config.py']}
    for wheel,names in wanted.items():
        b=(base/wheel).read_bytes()
        with zipfile.ZipFile(__import__('io').BytesIO(b)) as z:
            sources[wheel]=dict(sha256=sha(b),members={n:dict(sha256=sha(z.read(n)),lines=len(z.read(n).splitlines())) for n in names})
    readme=ROOT.parent/'official-inputs/HARNESS_README.md'
    sources['HARNESS_README.md']=dict(sha256=sha(readme.read_bytes()),lines=len(readme.read_bytes().splitlines()),
        source='https://www.kaggle.com/competitions/gemma-4-developer-agent/data',
        current_web_reader='Overview/evaluation/rules pages returned 0 body lines; no current-private-loader guarantee')
    (HERE/'OFFICIAL_SOURCE_PINS.json').write_text(json.dumps(sources,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(sessions=result['total_sessions'],tool_calls=result['total_tool_calls'],official_wheels=len(wanted))))


if __name__=='__main__':run()
