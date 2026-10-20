"""Independent posthoc evidence audit. Does not rerun tests or any Agent."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile
from harness_v2.evidence import read_events

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
RESULTS=HERE/'results/gpu01'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def emit(name, value):
    with (HERE/name).open('x',encoding='utf-8') as file:
        json.dump(value,file,indent=2,ensure_ascii=False);file.write('\n')


def summarize():
    plan=read(HERE/'AUTHORIZED_PROTOCOL.json')
    original=read(ROOT/'s2/egv_agenttool_t500_early_v01/GPU_MECHANISM_PROTOCOL_DRAFT.json')
    assert plan['runs']==original['runs'] and plan['candidates']==original['candidates']
    assert read(RESULTS/'model_identity.json')['files']==plan['model_files']
    assert read(RESULTS/'wheel_hashes.json')==plan['wheel_hashes']
    assert read(RESULTS/'task_wheel_hashes.json')==plan['task_wheel_hashes']
    with zipfile.ZipFile(RESULTS/'raw.zip') as z:
        for name,digest in plan['source_hashes'].items():
            assert sha(z.read('source/'+name))==digest,name
        executed_protocol=z.read('source/s2/early_gpu_protocol.json')
        assert sha(executed_protocol)==read(HERE/'EXECUTION_BUILD_MANIFEST.json')['authorized_protocol_sha256']
        assert json.loads(executed_protocol)==read(HERE/'AUTHORIZED_PROTOCOL.json')
    gate=read(RESULTS/'batch_gate.json')
    assert gate['infrastructure_passed'] and gate['stop_reason'] is None and not gate['not_run']
    assert len(gate['records'])==4 and read(RESULTS/'server_cleanup.json')['verified']
    records=[]
    for row in plan['runs']:
        folder=RESULTS/'runs'/f"{row['index']:02d}-{row['instance_id']}-{row['arm']}"
        tools=read(folder/'posthoc/tool_events.json')
        nested=read_events(folder/'nested_audit.jsonl')
        events=read_events(folder/'events.jsonl')
        native=read(folder/'official_result.json')
        audit=read(folder/'research_audit.json')
        descriptive=read(folder/'posthoc/descriptive.json')
        assert type(native['resolved']) is bool and native['resolved']==audit['official_resolved']
        assert native['test_exit_code']==audit['official_test_exit_code'] and audit['infrastructure_passed']
        assert read(folder/'worker_done.json')['cleanup_complete']
        junit=(folder/'phase2.junit.xml').read_bytes()
        capture=read(folder/'phase2_junit_capture.json')
        assert sha(junit)==capture['sha256'] and capture['sandbox_exists_at_capture']
        assert capture['capture_phase']=='before_native_sandbox_stop'
        tree=ET.fromstring(junit)
        cases=list(tree.iter('testcase'))
        counts=dict(tests=len(cases),passed=sum(not list(c) for c in cases),
            failures=sum(c.find('failure') is not None for c in cases),errors=sum(c.find('error') is not None for c in cases),
            skipped=sum(c.find('skipped') is not None for c in cases))
        target='rich/traceback.py' if row['instance_id'].startswith('rich_') else 'docs_src/metadata/tutorial001_1_py39.py'
        target_edits=[t for t in tools if target in t['changed_files']]
        target_reads=[t for t in tools if t['tool']=='read_file' and t['arguments'].get('filepath')==target]
        assert target_edits and target_reads
        edits_by_other=[t for t in tools if t['actor']!='main_coding_agent' and t['changed_files']]
        assert not edits_by_other
        tool_starts={r['call_id']:r for r in nested if r['kind']=='tool_start'}
        reads_seen=set();repeat_content=[];grep_seen=set();repeated_commands=[];bad_keys=[]
        for t in tools:
            if t['tool']=='read_file':
                extra=set(t['arguments'])-{'filepath','start_line','end_line'}
                if extra:bad_keys.append(dict(line=t['start_line'],extra_keys=sorted(extra)))
                content=t['result'].get('content','') if isinstance(t['result'],dict) else ''
                path=t['arguments'].get('filepath')
                key=(path,tool_starts[t['call_id']]['files'].get(path),sha(content.encode()))
                if key in reads_seen:repeat_content.append(t['start_line'])
                reads_seen.add(key)
            if t['tool']=='run_command':
                command=t['arguments'].get('command','')
                fingerprint=sha(json.dumps(tool_starts[t['call_id']]['files'],sort_keys=True).encode())
                key=(command,fingerprint)
                if key in grep_seen:repeated_commands.append(t['start_line'])
                grep_seen.add(key)
        requests=[r for r in read_events(folder/'http_wire.jsonl') if r['kind']=='http_request']
        terminal=[r for r in read_events(folder/'http_lifecycle.jsonl') if r['kind']=='terminal_status']
        assert {r['request_id'] for r in requests}=={r['request_id'] for r in terminal}
        assert len(requests)==len(terminal)==len({r['request_id'] for r in terminal})
        assert all(r['status']=='response_received' and isinstance(r.get('usage'),dict) and not r['partial_usage'] for r in terminal)
        withtools=[r for r in requests if r['body'].get('tools')]
        assert all(any(t.get('function',{}).get('name')=='egv_verifier' for t in r['body']['tools']) for r in withtools)
        for r in requests:
            body=r['body']
            assert body['model'].endswith('/gemma-4-31b-it-qat-w4a16-ct/2')
            assert body.get('seed')==17 and body.get('thinking_token_budget')==4096
            assert body.get('max_completion_tokens',body.get('max_tokens'))==16384
            assert all(body.get(k) is None for k in ('temperature','top_p','top_k'))
        context=[r for r in events if r['kind']=='context_admission']
        assert all(r['total_reserved']<=32768 for r in context if r['decision']=='allow')
        delegates=[r for r in nested if r['kind']=='tool_start' and r['tool']=='egv_verifier']
        assert not delegates and not any(r.get('actor')=='egv_verifier' for r in nested)
        patch=native['agent_patch']
        assert (folder/'latest.patch').read_bytes()==patch.encode()
        paths=[line.split(' b/',1)[1] for line in patch.splitlines() if line.startswith('diff --git ')]
        diag=[name for name in paths if name!=target]
        submissions=descriptive['submit_tool_events']
        first_submit=submissions[0]['end_seconds'] if submissions else None
        first=target_edits[0]
        record=dict(**row,native_resolved=native['resolved'],native_test_exit_code=native['test_exit_code'],JUnit=counts,
            task_target_source_path=target,
            task_target_kind='library implementation' if target.startswith('rich/') else 'executable documentation example, not fastapi library production code',
            first_target_file_read_seconds=target_reads[0]['end_seconds'],first_target_file_read_line=target_reads[0]['end_line'],
            first_target_source_edit_seconds=first['end_seconds'],first_target_source_edit_line=first['end_line'],
            last_target_source_edit_seconds=target_edits[-1]['end_seconds'],last_target_source_edit_line=target_edits[-1]['end_line'],
            first_edit_scope='Tool-completion/snapshot upper bound; Rich first field addition is not an already complete repair. Final applied candidate passes registered Phase2 only.',
            tool_starts_before_first_target_edit=sum(r['kind']=='tool_start' and r['monotonic']<tool_starts[first['call_id']]['monotonic'] for r in nested),
            target_edits=[dict(start_line=t['start_line'],end_line=t['end_line'],end_seconds=t['end_seconds']) for t in target_edits],
            first_explicit_submit_seconds=first_submit,successful_submit_calls=len(submissions),
            explicit_submit=bool(submissions),native_fallback=not bool(submissions),
            Agent_seconds=descriptive['Agent_elapsed_seconds'],Worker_seconds=gate['records'][row['index']-1]['result']['duration_seconds'],
            counted_tools=native['tool_calls'],actual_tool_starts=descriptive['actual_tool_start_events'],native_LLM_calls=native['total_llm_calls'],
            HTTP_dispatches=len(requests),HTTP_responses=len(terminal),cancelled_HTTP=0,usage_complete=True,
            HTTP_received_only_tokens=descriptive['HTTP_received_only_usage'],ADK_role_usage=descriptive['model_usage_by_role'],
            native_total_tokens_preserved=native['total_tokens'],Main_schema_requests=len(withtools),EGV_available_in_Main_schema=True,
            EGV_calls=0,EGV_model_calls=0,EGV_tool_calls=0,EGV_usage=None,
            EGV_counterevidence=0,EGV_delivered=0,EGV_closed_loops=0,EGV_closed_loop_rate=None,
            get_status_calls=sum(t['tool']=='get_status' for t in tools),
            error_tool_returns=[t['end_line'] for t in tools if isinstance(t['result'],dict) and t['result'].get('status')=='error'],
            identical_content_reads_same_file_version=repeat_content,
            identical_command_repeats_same_workspace=repeated_commands,
            ignored_or_unknown_read_argument_keys=bad_keys,
            final_patch_sha256=sha(patch.encode()),final_patch_bytes=len(patch.encode()),final_patch_paths=paths,
            final_unrelated_diagnostic_paths=diag,final_unrelated_diagnostic_count=len(diag),
            native_agent_boundary_error=read(folder/'agent_boundary.json')['agent_error'],
            observed_500s_time_deadline=False,native_JUnit_before_cleanup=True,
            evidence_root=str(folder.relative_to(HERE)).replace('\\','/'))
        records.append(record)
    totals={}
    for arm in ('A','B'):
        rows=[r for r in records if r['arm']==arm]
        totals[arm]=dict(tasks=len(rows),native_resolved=sum(r['native_resolved'] is True for r in rows),
            Agent_seconds=sum(r['Agent_seconds'] for r in rows),Worker_seconds=sum(r['Worker_seconds'] for r in rows),
            counted_tools=sum(r['counted_tools'] for r in rows),actual_tool_starts=sum(r['actual_tool_starts'] for r in rows),
            native_LLM_calls=sum(r['native_LLM_calls'] for r in rows),HTTP_dispatches=sum(r['HTTP_dispatches'] for r in rows),
            received_HTTP_tokens=sum(r['HTTP_received_only_tokens']['total_tokens'] for r in rows),
            explicit_submit_tasks=sum(r['explicit_submit'] for r in rows),explicit_submit_fraction=sum(r['explicit_submit'] for r in rows)/2,
            successful_submit_calls=sum(r['successful_submit_calls'] for r in rows),EGV_calls=0,closed_loop_rate=None,
            diagnostic_paths=sum(r['final_unrelated_diagnostic_count'] for r in rows))
    delta={key:totals['B'][key]-totals['A'][key] for key in ('Agent_seconds','Worker_seconds','counted_tools','native_LLM_calls','HTTP_dispatches','received_HTTP_tokens')}
    relative={key:delta[key]/totals['A'][key] for key in ('Agent_seconds','Worker_seconds','received_HTTP_tokens')}
    return dict(experiment_id=plan['experiment_id'],notebook='wudangdexiaodoashi/gemma4-s2-earlyegv-mechanism-01',saved_version=1,
        executed_Agent_runs=len(records),completed_Agent_runs=len(records),
        ordinary_failure_runs=sum(r['native_resolved'] is False for r in records),unknown_runs=0,not_run=0,
        native_pairs_both_resolved=sum(all(r['native_resolved'] for r in records if r['instance_id']==s['instance_id']) for s in plan['selected']),
        paired_success_difference=(totals['B']['native_resolved']-totals['A']['native_resolved'])/len(plan['selected']),population_resolution_rate=None,
        infrastructure_Go=True,stop_reason=None,records=records,arm_totals=totals,B_minus_A=delta,B_relative_to_A=relative,
        source_bindings_checked=len(plan['source_hashes']),model_files_checked=len(plan['model_files']),wheel_files_checked=len(plan['wheel_hashes']),
        total_HTTP_responses=sum(r['HTTP_responses'] for r in records),GPU_cancellation_exercised=False,
        shared_child_budget_GPU_exercised=False,reason='No child invocation; shared-budget behavior retains CPU evidence, not a new GPU child-boundary stress test.',
        algorithm_decision='NO_GO for expanded dual-Agent efficacy study on current evidence; no EGV mechanism observed, native outcomes tied, aggregate costs higher. Early edit/submit workflow signals are narrower and require isolated confirmation.')


if __name__=='__main__':
    result=summarize()
    emit('ANALYSIS_MEASUREMENTS.json',result)
    print(json.dumps(dict(completed=result['completed_Agent_runs'],EGV_calls=0,totals=result['arm_totals'],delta=result['B_minus_A'],relative=result['B_relative_to_A']),indent=2))
