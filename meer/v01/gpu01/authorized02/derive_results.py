"""Post-run measurement only. Requires an earlier outcome-blind review lock.

Never imported by a Notebook, candidate or Worker. Does not infer check relevance
or semantic correctness; those require the separate manual review and native result.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import zipfile

from .read_preflight import HERE, save


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def measure(archive):
    archive = Path(archive)
    lock = json.loads((HERE/'RELEVANCE_REVIEW_LOCK.json').read_bytes())
    assert lock['native_outcomes_read_before_lock'] is False
    assert lock['archive_sha256'] == sha(archive.read_bytes())
    for name, expected in lock['review_files'].items():
        assert sha((HERE/name).read_bytes()) == expected
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        names = set(z.namelist())

        def obj(name):
            return json.loads(z.read(name)) if name in names else None

        def rows(name):
            return [json.loads(x) for x in z.read(name).splitlines() if x.strip()] if name in names else None

        results=[]
        for name in sorted(n for n in names if n.endswith('/agent/adk_events.jsonl') and '/runs/' in n):
            prefix=name.removesuffix('agent/adk_events.jsonl')
            session=prefix.rstrip('/').rsplit('/',1)[-1]
            events=rows(name);wire=rows(prefix+'agent/http_wire.jsonl')
            calls=[];responses={}
            for i,row in enumerate(events):
                for part in row.get('event',{}).get('content',{}).get('parts',[]):
                    if part.get('function_call'):
                        calls.append(dict(part['function_call'],event_index=i,time=row.get('recorded_monotonic')))
                    if part.get('function_response'):
                        r=part['function_response'];responses[r.get('id')]=r
            agent=obj(prefix+'agent/agent_result.json') or {}
            native=obj(prefix+'official_result.json')
            journal=rows(prefix+'agent/events.jsonl') or []
            start=next((r['recorded_monotonic'] for r in journal if r.get('agent_started')),None)
            # Trusted snapshot deployment is an empty-to-populated tree before
            # Agent start. It must not count as a model production edit.
            changes=[r for r in journal if r.get('kind')=='source_boundary_observation'
                     and r.get('production_changed') and r.get('before')
                     and start is not None and r.get('start_monotonic',-1)>=start]
            request=[r for r in wire or [] if r.get('kind')=='http_request']
            response=[r for r in wire or [] if r.get('kind')=='http_response']
            successful=[r for r in response if r.get('status')==200]
            usages=[r.get('body',{}).get('usage') for r in successful]
            def subtotal(key):
                return sum(u[key] for u in usages) if usages and all(isinstance(u,dict) and isinstance(u.get(key),int) for u in usages) else None
            skill=[]
            for call in calls:
                if call['name']!='run_skill_script':continue
                r=responses.get(call.get('id'),{}).get('response',{})
                try:value=json.loads(r.get('stdout',''))
                except (ValueError,AttributeError):value={}
                allowed=('schema','verdict','prior_verdict','executed_assertions','failed_assertions',
                         'nonconstant_assertions','subprocess_invocations','source_sha256','check_sha256',
                         'evidence_fresh','source_unchanged_during_check','timed_out','wall_seconds',
                         'child_exit_code','exception_type','new_evidence')
                skill.append(dict(event_index=call['event_index'],time=call['time'],
                                  **{k:value[k] for k in allowed if k in value}))
            arm=session.rsplit('-',1)[-1]
            submits=[(i,c) for i,c in enumerate(calls) if c['name']=='submit_patch']
            successful_submits=[]
            for i,c in submits:
                r=responses.get(c.get('id'))
                if r:successful_submits.append(dict(event_index=c['event_index'],response=r.get('response')))
            finishes=Counter(c.get('finish_reason','UNKNOWN') for r in successful for c in r.get('body',{}).get('choices',[]))
            # Guard emits to the Worker journal, not the Agent sandbox journal.
            admissions=[r for r in rows(prefix+'events.jsonl') or [] if r.get('kind')=='context_admission']
            guards=[r for r in admissions if r.get('decision')=='reject']
            patch=prefix+'final.patch'
            results.append(dict(session=session,arm=arm,trace_sha256=sha(z.read(name)),
                agent_executed=bool(request),native_resolved=native.get('resolved') if native else None,
                native_TaskResult_sha256=sha(z.read(prefix+'official_result.json')) if native else None,
                trace_has_worker_done=prefix+'worker_done.json' in names,
                agent_error=agent.get('error'),agent_wall_seconds=agent.get('agent_seconds'),
                charged_tools=agent.get('charged_tools'),official_patch_submitted=agent.get('patch_submitted'),
                final_patch_sha256=sha(z.read(patch)) if patch in names else None,
                final_patch_bytes=len(z.read(patch)) if patch in names else None,
                tool_calls_by_name=dict(Counter(c['name'] for c in calls)),
                submit_calls=len(submits),submit_responses=successful_submits,
                post_first_submit_calls=len(calls)-submits[0][0]-1 if submits else None,
                Skill_invocations=len(skill),Skill_bypassed=(len(skill)==0) if arm!='A' and prefix+'worker_done.json' in names else None,
                verifier_events=skill,
                observed_newly_executed_assertions=sum(v.get('executed_assertions',0) for v in skill if v.get('subprocess_invocations',0)>0),
                source_changing_operations=len(changes),first_source_change_upper_bound_seconds=(changes[0]['end_monotonic']-start) if changes and start else None,
                meaningful_behavior_edit_seconds=None,
                real_HTTP_requests=len(request),HTTP_responses=len(response),HTTP_200=len(successful),
                observed_prompt_tokens=subtotal('prompt_tokens'),observed_completion_tokens=subtotal('completion_tokens'),
                observed_received_tokens=subtotal('total_tokens'),
                usage_complete=(len(request)==len(successful) and bool(usages) and all(u is not None for u in usages)),
                model_HTTP_seconds=sum(r.get('elapsed_seconds',0) for r in response),finish_reasons=dict(finishes),
                context_event_count=len(admissions),context_guard_triggered=bool(guards),
                context_rejections=[{k:r.get(k) for k in ('recorded_monotonic','input_tokens','output_reserved','safety_tokens','max_model_len','total_reserved','decision')} for r in guards],
                actual_counted_inputs=[r.get('input_tokens') for r in admissions],
                Agent_cleanup=obj(prefix+'agent/cleanup.json'),chroot_cleanup=obj(prefix+'agent/chroot_cleanup.json'),
                Verifier_cleanup=obj(prefix+'verifier/cleanup.json'),
                measurement_limits='Source change timing is an operation-end upper bound, not semantic repair proof. Missing usage is not zero. Submit response content requires success review.'))
        # Raw submit payloads belong in private evidence, not the public metrics.
        for row in results:
            row['submit_response_event_indices']=[r['event_index'] for r in row.pop('submit_responses')]
        save(HERE/'BATCH_02_DERIVED_METRICS.json',dict(archive_sha256=sha(archive.read_bytes()),
             review_lock_sha256=sha((HERE/'RELEVANCE_REVIEW_LOCK.json').read_bytes()),sessions=results))
    print(json.dumps(dict(sessions=len(results),outcomes=[dict(session=r['session'],resolved=r['native_resolved']) for r in results])))


if __name__=='__main__':
    import sys
    measure(sys.argv[1])
