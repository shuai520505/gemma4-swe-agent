"""Offline historical autopsy. Never execute archived commands or model code.

Public output contains hashes, timestamps and bounded derived observations only.
Raw action review files are written outside Git to --private-output.
"""
from __future__ import annotations
import argparse
import ast
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PARENT = ROOT.parent

SOURCES = [
    ('GPU03', 'private-evidence/u_re_real_gemma_abba03/read-06/evidence_confirmed/output/u_re_actionfirst_abba03.zip', '72030f1833ee6a8588087836bf281ae3aafae4c5a327b4f1d5651482aed7bea6'),
    ('V02B', 'private-evidence/u_re_v02b_gemma_batch01/read-04/evidence_confirmed/output/v02b-gemma-batch01.zip', '6ecb9bfceb0b230ea3f4a2281b219d1e94c1ff2e50d4b0960b8701b4e7af2e45'),
    ('V03', 'private-evidence/u_re_v03_context_gpu01/read-02/evidence_confirmed/output/v03-context-gpu01.zip', '05bbbe3626123f1c4dbc7ce01382867e2d84affca942314fda733b3692d50580'),
    ('CURE01', 'gemma4-swe-agent/cure/gpu-study-01/results/smoke/evidence.zip', '37c81c3cc89ddca69f8858f28015522f2f48af6e1781e1d44689885619c70639'),
    ('CURE_C1', 'gemma4-swe-agent/cure/gpu-study-02-c1/results/smoke/evidence.zip', '4108828cc749f81bb631bbfa2eab42138f794112e7def39daaff435300fe6e09'),
    ('S2_EARLY', 'gemma4-s1-score-optimization/s2/experiments/earlyegv_mechanism_01/results/gpu01/raw.zip', 'd51735ad43a2d6318c1ec7fb10bd607b7ba9906d268b3b87924d547445f08b68'),
    ('S2_T500', 'gemma4-s1-score-optimization/s2/experiments/t500_agenttool_smoke_01/results/gpu01/raw.zip', 'ee3651b4ca76b8a226a9f48ddb7e614add3bd32d3a77bcf32d37b13dd01425e0'),
    ('S1_OUTPUT', '@repo/s1/experiments/e1_outputcap_smoke_02/results/gpu/raw.zip', '6f7ce7cec7979921e8cfae11e3f80411f6398281f1c5a2e461b42a5a57b03128'),
    ('S1_LOCATE', '@repo/s1/experiments/e3_localize_smoke_03/results/gpu/raw.zip', '9279f95aadab5b4802c12bd4546ed78db44374173a451eb80bb9b66ce39c0159'),
    ('S1_STRUCTURED', '@repo/s1/experiments/e3_structured_smoke_04/results/gpu/raw.zip', 'a5e062da220fb9c0b0912006c5c1a82e3a7fd98eb75048614379cd0dfe07a2d5'),
    ('S1_EGV', '@repo/s1/experiments/egv_mechanism_smoke_01/results/gpu/raw.zip', 'fdb36179f46921b4d61362c2ecb406afb8167e8decfdfa6b44b60930347a73c5'),
]

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def digest(value):
    return sha(json.dumps(value, sort_keys=True, ensure_ascii=False).encode())

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8', newline='\n')

def production(path):
    return path.endswith('.py') and path.startswith(('fastapi/', 'rich/', 'src/requests/', 'requests/', 'lumen/', 'docs_src/'))

def pytest_summary(stdout):
    # Only the terminal summary, never traceback/assertion/test-parameter text.
    lines = [re.sub(r'\x1b\[[0-9;]*m', '', x).strip('= ') for x in stdout.splitlines()]
    line = next((x for x in reversed(lines) if re.fullmatch(r'(?:\d+ (?:passed|failed|errors?|skipped|xfailed|xpassed|warnings?)(?:, )?)+ in [\d.]+s(?: \([^)]*\))?', x)), '')
    return {k: int(v) for v,k in re.findall(r'(\d+) (passed|failed|errors|skipped|xfailed|xpassed)',line)}

def stop_class(error):
    text = str(error or '')
    if re.search('context|reservation',text,re.I) or ('"decision": "reject"' in text and 'output_reserved' in text): return 'CONTEXT_RESERVATION_STOP'
    if 'timeout' in text.lower(): return 'AGENT_TIMEOUT'
    if 'tool call budget' in text.lower(): return 'TOOL_BUDGET_EXHAUSTED'
    return 'OTHER_ERROR' if error else None

def candidate_identity(a, spec):
    directory = str(spec.get('agent_dir','')).split('/source/',1)
    if len(directory)!=2:return None, None
    prefix='source/'+directory[1].rstrip('/')+'/'
    members={n[len(prefix):]:sha(a.raw(n)) for n in sorted(a.names) if n.startswith(prefix) and not n.endswith('/')}
    if not members:return None, None
    for n in sorted(a.names):
        if not (n.startswith('source/') and n.endswith('.zip')):continue
        raw=a.raw(n)
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            if z.testzip():raise ValueError('Candidate CRC failure')
            hashes={p:sha(z.read(p)) for p in z.namelist() if not p.endswith('/')}
        if hashes==members:return sha(raw), hashes
    return None,members

def archived_task_identity(a, task, spec):
    found=[]
    def walk(o,member):
        if isinstance(o,list):
            for x in o:walk(x,member)
        elif isinstance(o,dict):
            if o.get('instance_id',o.get('task_id'))==task and (o.get('base_commit') or o.get('issue_sha256')):
                found.append((member,{k:o[k] for k in ['base_commit','issue_sha256','snapshot_sha256','task_record_sha256','test_patch_sha256','test_overlay_sha256','input_files'] if k in o}))
            for v in o.values():
                if isinstance(v,(dict,list)):walk(v,member)
    for n in sorted(a.names):
        if n.startswith('source/') and n.endswith(('SELECTED_TASKS.json','TASK_IDENTITY_LOCK.json')):walk(a.obj(n),n)
    merged=dict(base_commit=spec.get('base_commit'),issue_sha256=spec.get('problem_sha256'))
    for _,o in found:
        for k,v in o.items():
            if merged.get(k) is not None and merged[k]!=v:raise ValueError('Archived task identity conflict')
            merged[k]=v
    merged['identity_sources']=[n for n,_ in found]
    merged['verification_scope']='Archived identity records cross-checked; original external snapshots not re-downloaded.'
    return merged

def assertion_syntax(source):
    """Presence only; never equate AST assert with execution or relevance."""
    try:
        nodes = list(ast.walk(ast.parse(source)))
    except SyntaxError:
        return None
    asserts = [n for n in nodes if isinstance(n, ast.Assert)]
    return {'assert_nodes': len(asserts), 'nonconstant_assert_nodes': sum(not isinstance(n.test, ast.Constant) for n in asserts)}

def junit_counts(raw):
    # Never export test names, failure bodies, or hidden assertions.
    root = ET.fromstring(raw)
    cases = list(root.iter('testcase'))
    return dict(tests=len(cases), failures=sum(c.find('failure') is not None for c in cases),
                errors=sum(c.find('error') is not None for c in cases), skipped=sum(c.find('skipped') is not None for c in cases))

def joined_calls(adk):
    calls = []; responses = {}
    for i, row in enumerate(adk):
        for part in row.get('event', {}).get('content', {}).get('parts', []):
            if part.get('function_call'):
                calls.append(dict(part['function_call'], event_index=i, time=row['recorded_monotonic']))
            if part.get('function_response'):
                f = part['function_response']
                responses[f.get('id')] = dict(f, time=row['recorded_monotonic'], event_index=i)
    return calls, responses

def verdict(native, phase, count, requests):
    if not requests:
        return None, 'NO_REAL_MODEL_SESSION'
    if phase is None:
        return None, 'VERIFICATION_NOT_OBSERVED'
    if count and count['errors']:
        return native.get('resolved'), 'VERIFIER_ERRORS_ASSESSMENT_CONFOUNDED'
    return native.get('resolved'), 'NATIVE_RESULT_OBSERVED'

class Archive:
    def __init__(self, path, expected):
        raw = path.read_bytes()
        if sha(raw) != expected:
            raise ValueError(f'Archive digest mismatch: {path.name}')
        self.z = zipfile.ZipFile(path)
        if self.z.testzip() is not None:
            raise ValueError('Archive CRC failed')
        self.names = set(self.z.namelist()); self.reads = {}

    def raw(self, name):
        raw = self.z.read(name)
        self.reads[name] = dict(sha256=sha(raw), bytes=len(raw))
        return raw

    def obj(self, name, default=None):
        return json.loads(self.raw(name)) if name in self.names else default

    def rows(self, name):
        return [json.loads(x) for x in self.raw(name).splitlines() if x.strip()] if name in self.names else []

def run(private_output):
    sessions = []; excluded = []; inventory = []
    old_annotations = json.loads((ROOT/'u_re/v04/experiments/evidence_guided_repair_01/TRACE_BEHAVIOR_METRICS.json').read_bytes())
    ann = {(('V02B' if s['cohort']=='V02B_BATCH1' else s['cohort']), s['session']): s for s in old_annotations['sessions']}
    for cohort, location, expected in SOURCES:
        path = ROOT/location[6:] if location.startswith('@repo/') else PARENT/location
        if not path.exists():
            inventory.append(dict(cohort=cohort, path=location, status='MISSING', expected_sha256=expected)); continue
        a = Archive(path, expected)
        specs = {n: a.obj(n) for n in sorted(a.names) if re.match(r'^(results/)?specs/[^/]+\.json$', n)}
        for name in sorted(n for n in a.names if re.match(r'^(results/)?runs/[^/]+/(agent/)?adk_events\.jsonl$', n)):
            agent = name.removesuffix('adk_events.jsonl')
            pre = agent.removesuffix('agent/')
            label = pre.rstrip('/').split('/')[-1]
            native = a.obj(pre+'official_result.json', {})
            task = native.get('task_id') or re.search(r'(fastapi|rich|requests)_\d+', label)[0]
            spec_item = next(((n, s) for n,s in specs.items() if (s.get('instance_id')==task and (Path(n).stem==label or Path(n).stem==label[:2]))), (None,{}))
            specname, spec = spec_item
            adk = a.rows(name); calls, responses = joined_calls(adk)
            events = a.rows(agent+'events.jsonl')
            start = next((e['recorded_monotonic'] for e in events if e.get('agent_started')), None)
            wire = a.rows(agent+'http_wire.jsonl')
            req = [w for w in wire if w.get('kind')=='http_request']
            resp = [w for w in wire if w.get('kind')=='http_response']
            runtime = a.obj(pre+'runtime_config.json', {})
            result = a.obj(agent+'agent_result.json', {})
            boundary = a.obj(agent+'agent_boundary.json', {})
            audit = a.obj(pre+'audit_result.json', {})
            cleanup = a.obj(pre+'worker_done.json', {})
            phasepath = next((pre+s for s in ['verifier/phase2_execution.json','phase2_execution.json'] if pre+s in a.names), None)
            phase = a.obj(phasepath) if phasepath else None
            junitpath = next((pre+s for s in ['verifier/phase2.junit.xml','phase2.junit.xml'] if pre+s in a.names), None)
            counts = junit_counts(a.raw(junitpath)) if junitpath else None
            stdout = (phase or {}).get('stdout','')
            counts_text = pytest_summary(stdout)
            outcome, assessment = verdict(native,phase,counts,len(req))
            if counts_text.get('errors',0):
                assessment='VERIFIER_ERRORS_ASSESSMENT_CONFOUNDED'; outcome=None
            if cohort=='S1_EGV' and label.endswith('control'):
                # Independently read original JUnit; agent patch contains the invalid quoted docstring.
                xml=a.raw(junitpath).decode()
                if not all(x in xml for x in ['SyntaxError','applications.py','1367']):raise ValueError('Agent regression provenance changed')
                assessment='NATIVE_AGENT_REGRESSION_OBSERVED'
            rel = lambda t: t-start if t is not None and start is not None else None
            changes = [e for e in events if e.get('kind')=='source_boundary_observation' and start is not None and e.get('start_monotonic',-1)>=start and e.get('production_changed')]
            # Importing/copying the initial snapshot before Agent start is NOT an edit.
            source_changes = [dict(seconds=rel(e['end_monotonic']), monotonic=e['end_monotonic'],
                paths=e['production_changed'], before_sha256=digest(e['before']), after_sha256=digest(e['after']),
                interval_start_seconds=rel(e['start_monotonic']), basis='source_boundary_hash_change') for e in changes]
            nested = a.rows(pre+'nested_audit.jsonl'); before = {}
            if not source_changes and nested:
                for i,e in enumerate(nested):
                    key=e.get('call_id')
                    if e.get('kind')=='tool_start': before[key]=e
                    if e.get('kind')=='tool_end' and key in before:
                        b=before[key].get('files',{}); after=e.get('files',{})
                        if isinstance(b,dict) and isinstance(after,dict):
                            changed=[p for p in set(b)|set(after) if production(p) and b.get(p)!=after.get(p)]
                            if changed:source_changes.append(dict(seconds=rel(e['recorded_monotonic']),monotonic=e['recorded_monotonic'],paths=sorted(changed),before_sha256=digest(b),after_sha256=digest(after),basis='nested_tool_file_hash_change',event_index=i))
            private_rows=[]; public=[]; seen={}; edit_epochs=0; scripts={}; successful_submits=[]
            for c in calls:
                args=c.get('args') or {}; r=responses.get(c.get('id')); out=(r or {}).get('response') or {}
                command=args.get('command',''); filepath=args.get('filepath',''); text=json.dumps(out,sort_keys=True)
                ok=isinstance(out,dict) and out.get('status')=='ok'
                changed=[e for e in source_changes if c['time']<=e['monotonic']<=((r or {}).get('time',c['time']))]
                if not source_changes and c['name'] in ('edit_file','write_file') and production(filepath) and ok:
                    # Successful tool acknowledgement is weaker than a source hash observer.
                    changed=[dict(seconds=rel(r['time']),monotonic=r['time'],paths=[filepath],basis='tool_ack_only_hash_unavailable')]
                search=c['name']=='run_command' and bool(re.search(r'(^|[;&|\s])(rg|grep|find)\s',command))
                check=c['name']=='run_command' and bool(re.search(r'\b(pytest|unittest)\b|\bpython[\d.]*\s|\bassert\s',command))
                read=c['name']=='read_file' and production(filepath) and ok
                token=(command,digest(out),sum(e['monotonic']<=c['time'] for e in source_changes))
                repeated=bool(search and token in seen)
                if search:seen[token]=True
                broad=bool(check and re.search(r'(?:^|&&\s*|;\s*)(?:python[\d.]* -m )?pytest\s*$',command))
                if c['name']=='write_file' and ok:scripts[filepath]=args.get('content','')
                if c['name']=='edit_file' and ok and filepath in scripts:scripts[filepath]=scripts[filepath].replace(args.get('old_string',''),args.get('new_string',''))
                py=re.search(r'\bpython[\d.]*\s+([\w./-]+\.py)',command)
                asserted=assertion_syntax(scripts[py[1]]) if py and py[1] in scripts else None
                category='SEARCH' if search else 'SOURCE_READ' if read else 'CHECK_ATTEMPT' if check else 'EDIT' if changed else 'SUBMIT' if c['name']=='submit_patch' else 'OTHER'
                if c['name']=='submit_patch' and ok:successful_submits.append(c['time'])
                row=dict(event_index=c['event_index'],seconds=rel(c['time']),response_seconds=rel((r or {}).get('time')), tool=c['name'],
                    action_kind=category,args_sha256=digest(args),response_sha256=digest(out) if r else None,
                    response_observed=bool(r),production_mutation=bool(changed),source_change_basis=[e['basis'] for e in changed],
                    exact_repeated_search=repeated,unscoped_pytest=broad,check_script_assertion_syntax=asserted,
                    observed_path_error=bool(re.search(r'no such file or directory|file or directory not found',text,re.I)),
                    observed_dependency_error=bool(re.search(r'ModuleNotFoundError|No module named|fixture .* not found',text)),
                    test_relevance=None,semantic_information_gain=None)
                public.append(row);private_rows.append(dict(row,args=args,response=out))
            patchname=next((pre+s for s in ['final.patch','latest.patch'] if pre+s in a.names),None)
            patch=a.raw(patchname) if patchname else b''
            paths=re.findall(r'^\+\+\+ b/(.+)$',patch.decode('utf-8','replace'),re.M)
            usage=[w.get('body',{}).get('usage') for w in resp]; observed=[u for u in usage if isinstance(u,dict)]
            generation=[]
            for q in req:
                b=q.get('body',{});g={k:b.get(k) for k in ['model','max_tokens','max_completion_tokens','temperature','top_p','top_k','seed','thinking_budget','chat_template_kwargs','extra_body']}
                if g not in generation:generation.append(g)
            error=result.get('error') or boundary.get('agent_error') or native.get('error_message')
            error_class=stop_class(error)
            annotation=ann.get((cohort,label))
            if annotation and annotation['raw_events_sha256']!=sha(a.raw(name)):raise ValueError('Historical annotation trace mismatch')
            # Recheck historical event labels against original serialized calls, not blind summary trust.
            if annotation:
                for old,new,original in zip(annotation['events'],public,calls):
                    if old['event_index']!=new['event_index'] or old['args_sha256']!=sha(json.dumps(original.get('args') or {},sort_keys=True).encode()):raise ValueError('Annotation event identity mismatch')
                if len(annotation['events'])!=len(public):raise ValueError('Annotation event count mismatch')
            first_edit = min((e['seconds'] for e in source_changes),default=None)
            if first_edit is None:first_edit=next((x['response_seconds'] for x in public if x['production_mutation']),None)
            first_read=next((x['response_seconds'] for x in public if x['action_kind']=='SOURCE_READ'),None)
            zipsha,memberhashes=candidate_identity(a,spec)
            summary=dict(id=cohort+'/'+label,cohort=cohort,session=label,task=task,
                sample_kind='OWNED_SYNTHETIC' if cohort.startswith('CURE') else 'PUBLIC_SWE_DEVELOPMENT',
                repository=native.get('repo'),candidate_label=label.split('-',2)[-1],
                candidate_zip_sha256=zipsha,candidate_member_sha256=memberhashes or runtime.get('candidate_hashes') or spec.get('candidate_hashes'),
                task_identity=dict(archived_task_identity(a,task,spec),source_spec=specname),
                issue_contract_summary=None,issue_category=None,first_concrete_hypothesis=None,
                source_archive_sha256=expected,raw_trace_member=name,raw_trace_sha256=sha(a.raw(name)),
                agent_start_monotonic=start,timestamp_semantics='Within-session monotonic seconds; operation completion is an observation upper bound, not exact edit instant.',
                real_model_requests=len(req),received_http_responses=len(resp),actual_model_inference=bool(resp),
                native_resolved=outcome,native_raw_resolved=native.get('resolved'),native_assessment=assessment,
                native_result_member=pre+'official_result.json',native_result_sha256=sha(a.raw(pre+'official_result.json')),
                junit_member=junitpath,junit_sha256=sha(a.raw(junitpath)) if junitpath else None,junit_counts=counts,
                native_execution_member=phasepath,native_summary_counts=counts_text,
                model_request_config_variants=generation,runtime_budget=runtime.get('research_config') or runtime.get('budget'),
                first_implementation_read_seconds=first_read,implementation_relevance='Production namespace read; precise task relevance requires reviewed annotation.',
                first_production_edit_seconds=first_edit,first_behavioral_edit_seconds=annotation.get('first_target_behavior_edit_seconds') if annotation else None,
                first_check_attempt_seconds=next((x['seconds'] for x in public if x['action_kind']=='CHECK_ATTEMPT'),None),
                first_discriminating_check_seconds=None,source_changes=source_changes,
                final_patch_sha256=sha(patch) if patchname else None,final_patch_bytes=len(patch) if patchname else None,
                final_production_paths=[p for p in paths if production(p)],final_other_file_count=sum(not production(p) for p in paths),
                successful_submit_count=len(successful_submits),post_submit_tool_calls=sum(c['time']>successful_submits[0] for c in calls) if successful_submits else None,
                official_charged_tools=result.get('charged_tools',native.get('tool_calls')),observed_tool_calls=len(calls),
                received_usage={k:sum(u[k] for u in observed if u.get(k) is not None) if observed and all(u.get(k) is not None for u in observed) else None for k in ['prompt_tokens','completion_tokens','total_tokens']},
                usage_missing_response_count=sum(u is None for u in usage),unanswered_requests=max(0,len(req)-len(resp)),
                agent_seconds=result.get('agent_seconds',next((e['agent_elapsed_seconds'] for e in events if e.get('agent_elapsed_seconds') is not None),None)),worker_seconds=audit.get('duration_seconds'),native_seconds=native.get('duration_seconds'),
                stop_class=error_class,cleanup_complete=cleanup.get('cleanup_complete',audit.get('cleanup_complete')),
                exact_repeated_search_count=sum(x['exact_repeated_search'] for x in public),unscoped_pytest_count=sum(x['unscoped_pytest'] for x in public),
                path_error_actions=sum(x['observed_path_error'] for x in public),dependency_error_actions=sum(x['observed_dependency_error'] for x in public),
                first_read_to_edit_seconds=first_edit-first_read if first_edit is not None and first_read is not None else None,
                reviewed_historical_annotation=bool(annotation),events=public,
                failure_labels=[],limits=['Nonempty patch and source edit are not correctness evidence.','No intermediate native verification: losing a correct patch cannot be inferred from final failure.'])
            write(private_output/(cohort+'-'+label+'.json'),dict(summary=summary,actions=private_rows))
            if req:sessions.append(summary)
            else:excluded.append(summary)
        original_manifest=a.obj('evidence_manifest.json',{})
        checked=0
        for n,m in list(a.reads.items()):
            if n in original_manifest and isinstance(original_manifest[n],dict) and original_manifest[n].get('sha256'):
                if original_manifest[n]['sha256']!=m['sha256']:raise ValueError('Original member manifest mismatch')
                checked+=1
        inventory.append(dict(cohort=cohort,path=location,status='SHA256_AND_CRC_VERIFIED',sha256=expected,bytes=path.stat().st_size,original_manifest_consumed_members_checked=checked,read_members=a.reads))
        a.z.close()
    write(HERE/'EVIDENCE_MANIFEST.json',dict(base_commit='f8b63e9db3d97760d1798fe12dfd5139871dcdc0',archives=inventory))
    data=dict(schema_version=1,scope='All real-model sessions in the 11 enumerated accessible GPU archives; CPU/baseline/probe and undispatched slots excluded.',
        sessions=sessions,excluded_preinference_workers=excluded,summary=dict(real_model_sessions=len(sessions),raw_native_boolean_count=sum(isinstance(s['native_raw_resolved'],bool) for s in sessions),
        interpretable_native_assessment_count=sum(s['native_assessment'] in ('NATIVE_RESULT_OBSERVED','NATIVE_AGENT_REGRESSION_OBSERVED') for s in sessions),tools=sum(s['observed_tool_calls'] for s in sessions),cohorts=dict(Counter(s['cohort'] for s in sessions))))
    write(HERE/'TRAJECTORY_DATASET.json',data)
    print(json.dumps(data['summary']))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--private-output',type=Path,required=True)
    args=parser.parse_args()
    if ROOT in args.private_output.resolve().parents:raise SystemExit('Raw outputs must be outside repository')
    run(args.private_output)
