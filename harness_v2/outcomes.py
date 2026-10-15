"""Audit classifications are separate from immutable official result fields."""
from collections import Counter
import re


def normalize(raw, *, started, stage=None):
    if not started:
        return dict(status='not_run', failure_stage=None, reason='not_started')
    if raw is None:
        return dict(status='unknown', failure_stage=stage, reason='official_result_missing')
    error=str(raw.get('error') or raw.get('error_message') or '')
    code=raw.get('test_exit_code')
    output=raw.get('test_output') or ''
    if raw.get('resolved') is True:
        return dict(status='resolved', failure_stage=None, reason='official_resolved')
    if code==124:
        return dict(status='unknown',failure_stage='verification',reason='timeout')
    if error.startswith('Failed to apply agent patch'):
        return dict(status='failed',failure_stage='apply_patch',reason='agent_patch_rejected')
    invoked=output.startswith('STDOUT:\n') and '\nSTDERR:\n' in output
    if invoked and code in (3,4,5):
        return dict(status='unknown',failure_stage='verification',reason='verifier_internal_usage_or_no_tests_error')
    if invoked and type(code) is int and code in (1,2):
        collection=bool(re.search(r'ERROR collecting|errors? during collection',output,re.I))
        return dict(status='failed',failure_stage='test_collection' if collection else 'verification',
                    reason='collection_failure' if collection else 'nonzero_test_exit')
    if re.search(r'timed?\s*out|timeout|time budget', error, re.I):
        return dict(status='unknown',failure_stage='agent',reason='timeout')
    return dict(status='unknown',failure_stage=stage,reason='no_confirmed_verdict')


def summarize(rows, *, planned_per_arm):
    result={}
    for arm,n in planned_per_arm.items():
        selected=[r for r in rows if r['arm']==arm]
        c=Counter(r['status'] for r in selected)
        missing=max(0,n-len(selected))
        c['not_run']+=missing
        complete=len(selected)==n and not c['unknown'] and not c['not_run']
        result[arm]=dict(planned=n,**{k:c[k] for k in ('resolved','failed','unknown','not_run')},
            complete=complete,resolution_rate=c['resolved']/n if n and complete else None)
    if not all(arm['complete'] for arm in result.values()):
        for arm in result.values(): arm['resolution_rate']=None
    return result
