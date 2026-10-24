"""Human-reviewed labels bound to independently parsed action indices and hashes.

This is an offline research annotation, NEVER an Agent runtime controller.
Labels are nonexclusive. Missing semantic measurements remain null.
"""
import json
import zipfile
from collections import Counter
from pathlib import Path
from audit import HERE, ROOT, PARENT, SOURCES, write

# Relevant read index, first behavioral edit index, supported categories, audit note.
REVIEWS = {
 'GPU03/01-fastapi_9425-A': (18,None,['F5','F7'], 'e30/32 reproduction tests a neighboring annotation case, not the stringified case in the Issue; no production edit before guard.'),
 'GPU03/02-fastapi_9425-B': (20,43,[], 'e26/28 distinguishes annotation representations; e43 edits; e45/e51 check changed behavior; e73 submits. Native passes.'),
 'GPU03/03-fastapi_14786-B': (2,8,['F5'], 'e6 fails an assertion, e8 edits, e10 passes the same check. Later unscoped pytest and nonexistent path are unnecessary detours, despite native success.'),
 'GPU03/04-fastapi_14786-A': (2,8,['F7'], 'Fail/edit/pass sequence precedes successful submission. e38 submit, e40/e42 reads, e44 repeat submit, e46 status; guard stops a natively correct patch.'),
 'V02B/01-fastapi_5077-A': (6,None,['F7'], 'Self-authored reproduction initially fails on assignment to a read-only attribute. Later printed success coexists with unresolved annotation output; no production edit. Whether the model accepted that output is unknown.'),
 'V02B/02-fastapi_5077-B': (10,None,['F5','F7'], 'e24 creates a test body containing pass without a discriminating assertion; e26/e30 green. e32 changes production only to add debug output, not repair behavior.'),
 'V02B/03-fastapi_11355-B': (40,None,['F7'], 'Multiple self-authored examples and caught errors precede relevant helper inspection; no production edit. Issue lacks a complete executable contract. Exact causal misunderstanding is unobservable.'),
 'V02B/04-fastapi_11355-A': (28,42,['F5','F7'], 'e40 fails an annotation assertion, e42 changes its handling, e44 reads modified code; guard prevents any later execution. Local hypothesis relevance to the entire Issue remains unproven.'),
 'V03/01-fastapi_5077-A': (6,36,[], 'Cross-module reproducer output changes after e36/e38; native passes. Guard stops the session before explicit submit; official fallback retains a correct patch.'),
 'V03/02-fastapi_5077-B': (6,28,['F5'], 'e28/e30 behavior edits; e32 changed reproduction output. e36 unscoped pytest collects 702 cases/162 errors, e38 invalid path; e48/e50 relevant tests pass and e54 submits.'),
 'V03/03-fastapi_11355-B': (36,74,['F5','F6','F7'], 'e18 and e70 repeat a negative query; many ordinary examples do not distinguish the intended defect. e72 import-only edit, e74 first behavioral edit near 288s, e76 another edit near 299s; no post-edit execution. F6 is interpretation, not proof all exploration was waste.'),
 'V03/04-fastapi_11355-A': (42,None,['F7'], 'Relevant implementation was inspected; ordinary examples and searches continue until guard. No production edit; no observable proof of a correct causal explanation.'),
 'CURE01/01-lumen_interface_01-checklist': (None,'first',[''], 'Owned synthetic migration task; reads implementation/caller, adds compatible API/export, checks and submits. Not independent SWE evidence.'),
 'CURE_C1/01-lumen_interface_01-checklist': (None,'first',[], 'Owned synthetic task; repeat submission follows removal of own scratch file, so post-submit work is not automatically waste.'),
 'CURE_C1/02-lumen_interface_01-cure_v01_c1': (None,'first',[], 'Same owned synthetic repair. Model JSON declarations are advisory; no global state controller was executed.'),
 'S2_EARLY/01-rich_3676-A': (None,'first',['F7'], '500s/60-tool experiment; production repair late, original tests pass. Tool cap prevents explicit submission; fallback patch succeeds. No AgentTool delegation.'),
 'S2_EARLY/02-rich_3676-B': (None,'first',[], '500s experiment; earlier behavioral edits and explicit submission. Reproduction/API mistakes occur but native passes. No AgentTool delegation.'),
 'S2_EARLY/03-fastapi_14492-B': (8,12,['F7'], 'Task target is executable docs_src example, not fastapi library. Edits that example; native passes. Three successful submits and six post-submit tools. Visible workspace test edit is not a trusted verifier modification.'),
 'S2_EARLY/04-fastapi_14492-A': (24,38,[], 'Reads and edits target docs_src example, submits without running pytest; native passes. Absence of local test does not imply incorrect patch.'),
 'S2_T500/01-rich_3471-B': (6,90,['F5','F7'], 'Production edit after ~464s; a self-authored check has 3 pass/1 fail based on an unsupported control-character expectation. Native 108 pass. Deadline prevents submission; no AgentTool invocation.'),
 'S1_OUTPUT/01-requests_7328-control': (None,36,['F5','F7','F8'], 'Post-edit reproduction still reports the investigated symptom; replacement mock yields a vacuous-looking history result. Native has 194 fixture errors, so repair outcome is unknown, not an algorithm failure.'),
 'S1_LOCATE/01-rich_3278-control': (None,'first',['F7'], 'Final native summary is 4 failed/19 passed, zero errors. Historical observer confused a test data string saying 4 errors with an environment failure; its suppression of the next arm is infrastructure error, not this task classification.'),
 'S1_STRUCTURED/01-rich_3130-control': (None,44,['F4','F5','F6','F7'], 'e22 reproduction calls nonexistent API; e44 behavioral edit; e52/e54/e56 repeat the same failing targeted pytest with no intervening edit, then no revision. This supports failure to use feedback, not an inferred internal belief.'),
 'S1_STRUCTURED/02-rich_3130-e3_locate': (None,54,['F3','F5','F7'], 'Initial ~79s edit is debug only. e54/e56 behavioral edits introduce an AttributeError observed at e58; e60 fixes it, e62 runs. Later inclusion-only assertions pass but native fails. This is actual revision, not F4 failure.'),
 'S1_EGV/01-fastapi_15800-egv': (None,38,['F7'], 'e42 targeted HTTP assertions fail; e44/e46 revise; e48 three checks pass; e52 repeats unchanged checks. Native 18 pass/42 fail: feedback-driven local correction is insufficient for complete repair.'),
 'S1_EGV/02-fastapi_15800-control': (None,84,['F3','F5','F7'], 'Late production edits introduce literal escaped docstring quotes. No execution after edits. Original native JUnit reports SyntaxError at the changed applications.py location; algorithm-generated regression, not missing dependency.'),
}

CONTRACTS = {
 'fastapi_9425': ('annotation normalization','Consistent handling of stringified and literal absent return annotations.'),
 'fastapi_14786': ('credential parsing','Robust parsing of the documented credential separator behavior; Issue already gives unusually explicit implementation guidance.'),
 'fastapi_5077': ('wrapped callable annotations','Resolve wrapped callable annotations in the appropriate defining context.'),
 'fastapi_11355': ('annotation compatibility','Correct stringified-annotation behavior on the stated Python version; Issue is brief and links external context.'),
 'fastapi_14492': ('documentation example API','Update the metadata example to demonstrate the documented API option.'),
 'rich_3676': ('rendering robustness','Avoid renderer failure for traceback input with unusually long lines.'),
 'rich_3471': ('text token handling','Handle control characters consistently in token append operations.'),
 'rich_3278': ('escape decoding','Remove the relevant private/alternate ANSI escape sequences correctly.'),
 'rich_3130': ('text aggregation','Retain all fragments when composing multi-fragment text, including required formatting semantics.'),
 'requests_7328': ('redirect history','Avoid a response containing itself in redirect history without breaking redirect behavior.'),
 'fastapi_15800': ('frontend API','Implement the requested frontend-serving interface with the full specified behavior.'),
 'lumen_interface_01': ('owned synthetic API migration','Add compatible entry point and export while preserving an existing caller.'),
}

def run():
    data=json.loads((HERE/'TRAJECTORY_DATASET.json').read_bytes())
    source_paths={c:(ROOT/l[6:] if l.startswith('@repo/') else PARENT/l) for c,l,_ in SOURCES}
    timelines=['# Observable repair timelines\n', 'All times below are seconds from the archived Agent start. Tool completion bounds the edit time; it is not an instruction-level clock. Event indices are zero-based ADK JSONL row indices. Full public event hashes are in TRAJECTORY_DATASET.json. Raw commands, patches and test text remain private.\n']
    for s in data['sessions']:
        read,edit,labels,note=REVIEWS[s['id']]
        events=s['events']; byindex={e['event_index']:e for e in events}
        if read is None:
            read=next((e['event_index'] for e in events if e['action_kind']=='SOURCE_READ'),None)
        if edit=='first':edit=next((e['event_index'] for e in events if e['production_mutation']),None)
        # Reviewed indices must identify actual calls. Never invent a missing event.
        for idx in [read,edit]:
            if idx is not None and idx not in byindex:raise ValueError((s['id'],idx))
        s['reviewed_relevant_read_event']=read
        s['first_relevant_inspection_seconds']=byindex[read]['response_seconds'] if read is not None else None
        s['reviewed_behavioral_edit_event']=edit
        s['first_behavioral_edit_seconds']=byindex[edit]['response_seconds'] if edit is not None else None
        s['behavioral_edit_definition']='Observed modification intended to change task behavior, including a task-targeted documentation example; NOT proof of semantic correctness. Debug/import-only edits excluded.'
        s['failure_labels']=[x for x in labels if x]
        s['failure_label_status']={x:('INTERPRETATION' if x=='F6' and s['cohort']=='V03' else 'OBSERVED_EVENT_PATTERN') for x in s['failure_labels']}
        s['review_note']=note
        s['issue_category'],s['issue_contract_summary']=CONTRACTS[s['task']]
        s['production_edit_acknowledgements']=[{'event_index':e['event_index'],'seconds':e['response_seconds'],'basis':e['source_change_basis']} for e in events if e['production_mutation']]
        s['check_attempt_events']=[e['event_index'] for e in events if e['action_kind']=='CHECK_ATTEMPT']
        t=s['first_behavioral_edit_seconds']
        s['tools_started_before_first_behavior_edit']=sum(e['seconds'] is not None and e['seconds']<t for e in events) if t is not None else None
        with zipfile.ZipFile(source_paths[s['cohort']]) as z:
            wire_name=s['raw_trace_member'].replace('adk_events.jsonl','http_wire.jsonl')
            wire=[json.loads(x) for x in z.read(wire_name).splitlines() if x.strip()]
        before=[x for x in wire if x.get('kind')=='http_response' and t is not None and x['recorded_monotonic']-s['agent_start_monotonic']<=t]
        usages=[x.get('body',{}).get('usage',{}).get('total_tokens') for x in before]
        s['tokens_received_before_first_behavior_edit']=sum(usages) if t is not None and usages and all(x is not None for x in usages) else None
        s['pre_edit_token_semantics']='Received response usage only; excludes unanswered requests, includes any observed compression calls; no estimate for unavailable usage.'
        s['lost_previously_correct_patch']=None
        s['semantic_information_gain_count']=None
        timelines += [f"## {s['id']}\n",f"Source `{s['source_archive_sha256']}` / `{s['raw_trace_member']}`; trace SHA `{s['raw_trace_sha256']}`. Candidate ZIP `{s['candidate_zip_sha256']}`.\n",
            f"Relevant inspection: {s['first_relevant_inspection_seconds']} (e{read}); first observed file edit: {s['first_production_edit_seconds']}; first behavioral edit: {t} (e{edit}). Checks: {s['check_attempt_events']}. All subsequent edit acknowledgements: {s['production_edit_acknowledgements']}.\n",
            f"Native raw={s['native_raw_resolved']}, assessed={s['native_resolved']} ({s['native_assessment']}); submits={s['successful_submit_count']}; post-submit tools={s['post_submit_tool_calls']}; stop={s['stop_class']}. Model requests={s['real_model_requests']}; received usage={s['received_usage']}; tools={s['observed_tool_calls']}; Agent seconds={s['agent_seconds']}.\n",note+'\n']
    failures=[s for s in data['sessions'] if s['native_resolved'] is False]
    successes=[s for s in data['sessions'] if s['native_resolved'] is True]
    data['review_summary']={
        'assessed_failures':len(failures),'assessed_successes':len(successes),'unknown_outcomes':sum(s['native_resolved'] is None for s in data['sessions']),
        'failure_label_counts_in_assessed_failures':dict(Counter(x for s in failures for x in s['failure_labels'])),
        'failures_with_relevant_inspection':sum(s['first_relevant_inspection_seconds'] is not None for s in failures),
        'behavior_edits_all_sessions':sum(s['first_behavioral_edit_seconds'] is not None for s in data['sessions']),
        'behavior_edits_failures':sum(s['first_behavioral_edit_seconds'] is not None for s in failures),
        'behavior_edits_successes':sum(s['first_behavioral_edit_seconds'] is not None for s in successes),
        'native_correct_without_submit':sum(s['successful_submit_count']==0 for s in successes),
        'semantic_information_gain_frequency':None,
        'known_correct_patch_later_lost_count':None,
        'limits':'Descriptive selected historical development sample; nonexclusive labels, no pooled treatment effect. F7 means budget/closure limitation co-occurred with unresolved work, not that longer runtime would fix it.'}
    write(HERE/'TRAJECTORY_DATASET.json',data)
    (HERE/'TRAJECTORY_TIMELINES.md').write_text('\n'.join(timelines),encoding='utf-8',newline='\n')
    print(json.dumps(data['review_summary']))

if __name__=='__main__':run()
