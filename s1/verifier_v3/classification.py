"""Structured Pytest events and conservative attribution. No free-text error scanner."""
from collections import Counter
import re
import xml.etree.ElementTree as ET


def terminal_summary(stdout):
    """Parse only the terminal reporter's final statistics line, never traceback text."""
    rows=[line.strip() for line in stdout.splitlines() if line.strip()]
    if not rows:return None
    line=re.sub(r'\x1b\[[0-9;]*m','',rows[-1]).strip('= ')
    match=re.fullmatch(r'(.+?) in [0-9.]+s(?: \([0-9:]+\))?',line)
    if not match:return None
    counts=Counter()
    for part in match[1].split(', '):
        token=re.fullmatch(r'(\d+) (passed|failed|errors?|skipped|xfailed|xpassed|deselected|warnings?|reruns?)',part)
        if not token:return None
        name=token[2].rstrip('s') if token[2] in ('errors','warnings','reruns') else token[2]
        counts[name]+=int(token[1])
    return dict(counts)


def junit_events(raw):
    if not raw or len(raw)>16*1024*1024 or b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():
        raise ValueError('Missing, oversized or unsafe JUnit')
    root=ET.fromstring(raw)
    suites=[root] if root.tag=='testsuite' else list(root.findall('testsuite')) if root.tag=='testsuites' else []
    if not suites:raise ValueError('Unsupported JUnit root')
    events=[];totals=Counter()
    for suite in suites:
        actual=Counter(tests=0,failures=0,errors=0,skipped=0)
        for case in suite.findall('testcase'):
            nodes=[n for n in case if n.tag in ('failure','error','skipped')]
            if len(nodes)>1:raise ValueError('Ambiguous multi-outcome testcase')
            actual['tests']+=1
            event=dict(classname=case.get('classname',''),name=case.get('name',''))
            if not nodes:event['category']='passed'
            else:
                node=nodes[0];message=node.get('message','')
                event.update(message=message,details=node.text or '',type=node.get('type',''))
                if node.tag=='failure':
                    event['category']='assertion_failure';actual['failures']+=1
                elif node.tag=='skipped':event['category']='skipped';actual['skipped']+=1
                else:
                    actual['errors']+=1
                    if message=='collection failure':event['category']='collection_error'
                    elif message=='internal error' and case.get('classname')=='pytest' and case.get('name')=='internal':
                        event['category']='internal_error'
                    elif message.startswith('failed on setup with '):event.update(category='setup_error',phase='setup')
                    elif message.startswith('failed on teardown with '):event.update(category='setup_error',phase='teardown')
                    else:event['category']='unknown_unparsed'
            events.append(event)
        for key in ('tests','failures','errors','skipped'):
            if int(suite.get(key,'-1'))!=actual[key]:raise ValueError('JUnit aggregate mismatch:'+key)
        totals.update(actual)
    return dict(totals),events


def blocked(category,reason,**extra):
    return dict(category=category,categories=[category],attribution='unknown',
        infrastructure_stop=True,confirmed_failure=False,reason=reason,**extra)


def classify(execution,junit=None,*,baseline=None,historical_legacy=False):
    """Historical nonzero fallback is read-only; never an admission or success route."""
    if not execution:return blocked('verifier_execution_error','Native Phase2 execution absent')
    code=execution.get('exit_code')
    if type(code) is not int or code not in (0,1,2,3):
        return blocked('verifier_execution_error','Native execution timeout/signal/usage/exception',exit_code=code)
    summary=terminal_summary(execution.get('stdout',''))
    if junit is None and historical_legacy and code!=0:
        # Old native SDK discarded XML on failure. Require terminal counts AND
        # actual Pytest reporter sections, not error words embedded in data.
        lines=execution.get('stdout','').splitlines()
        if code==1 and summary and summary.get('failed',0)>0 and not summary.get('error',0):
            if not any(line.startswith('FAILED ') for line in lines):return blocked('unknown_unparsed','No legacy failure reporter entries')
            counts=dict(tests=sum(summary.get(k,0) for k in ('passed','failed','skipped','xfailed','xpassed')),
                failures=summary['failed'],errors=0,skipped=summary.get('skipped',0)+summary.get('xfailed',0))
            events=[dict(category='assertion_failure')]
        elif code==1 and summary and summary.get('error',0):
            headers=[line for line in lines if re.fullmatch(r'_+ ERROR at (?:setup|teardown) of .+ _+',line.strip())]
            if len(headers)!=summary['error']:return blocked('unknown_unparsed','Legacy error stages not proven')
            counts=dict(tests=sum(summary.get(k,0) for k in ('passed','failed','error','skipped','xfailed','xpassed')),
                failures=summary.get('failed',0),errors=summary['error'],skipped=summary.get('skipped',0)+summary.get('xfailed',0))
            events=[dict(category='setup_error')]
            if counts['failures']:events.append(dict(category='assertion_failure'))
        else:return blocked('unknown_unparsed','Unsupported legacy output; no success inferred')
        level='legacy_nonzero_native_summary_readonly'
    else:
        try:counts,events=junit_events(junit)
        except (ValueError,ET.ParseError,TypeError) as exc:return blocked('unknown_unparsed','JUnit invalid:'+str(exc))
        level='original_JUnit'
        cats={e['category'] for e in events}
        if 'unknown_unparsed' in cats:return blocked('unknown_unparsed','JUnit error stage unrecognized',events=events)
        if code==3:
            if 'internal_error' not in cats:return blocked('unknown_unparsed','Exit3 without structured internal error')
        else:
            if not summary:return blocked('unknown_unparsed','Terminal Pytest statistics absent')
            if (counts['failures']!=summary.get('failed',0) or counts['errors']!=summary.get('error',0)
                or counts['skipped']!=summary.get('skipped',0)+summary.get('xfailed',0)
                or counts['tests']-counts['failures']-counts['errors']-counts['skipped']!=summary.get('passed',0)+summary.get('xpassed',0)):
                return blocked('unknown_unparsed','JUnit/stdout counts contradict',counts=counts,summary=summary)
            if code==0 and (counts['errors'] or counts['failures'] or not counts['tests'] or counts['tests']==counts['skipped']):
                return blocked('unknown_unparsed','Exit0 without real passing tests')
            if code==1 and not (counts['failures'] or counts['errors']):return blocked('unknown_unparsed','Exit1 without failures/errors')
            if code==2 and 'collection_error' not in cats:return blocked('unknown_unparsed','Exit2 without collection event')
    cats=sorted({e['category'] for e in events})
    errors=any(c in cats for c in ('setup_error','collection_error','internal_error'))
    primary=next((c for c in ('internal_error','collection_error','setup_error','assertion_failure','passed') if c in cats),'unknown_unparsed')
    baseline=baseline or {}
    if errors:
        environment=baseline.get('environment_blocked_verified') is True and baseline.get('matching_callchain_verified') is True
        attribution='environment' if environment else 'unknown_requires_baseline_and_callchain'
        stop=True;reason='Known clean-baseline environment blocker' if environment else 'Error event does not by itself prove external environment'
    else:attribution='test_call_failure' if counts['failures'] else 'no_test_failures';stop=False;reason='Structured native test outcome'
    return dict(category=primary,categories=cats,counts=counts,summary=summary,events=events,
        attribution=attribution,infrastructure_stop=stop,confirmed_failure=bool(counts['failures'] and not errors),
        reason=reason,evidence_level=level,exit_code=code,historical_only=historical_legacy)
