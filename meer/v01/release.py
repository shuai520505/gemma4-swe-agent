"""Build safe derived reports from independently audited private CPU evidence."""
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile
from .build import HERE,ROOT,sha


def write(name,text):
    (HERE/name).write_text(text,encoding='utf-8',newline='\n')


def release():
    proof=json.loads((HERE/'CPU_ACCEPTANCE_CPU03.json').read_bytes())
    assert proof['status']=='MEER_CPU_ENGINEERING_PASS'
    lock=json.loads((HERE/'CANDIDATE_MANIFEST.json').read_bytes())
    records=proof['records'];b=records[1];c=records[2];bypass=records[3]
    history=json.loads((HERE/'HISTORY_INTEGRITY.json').read_bytes())
    for row in history['baselines']:
        assert sha((ROOT/row['path']).read_bytes())==row['ZIP_sha256']
    assert b['schemas']==c['schemas'] and b['compiled'][0]['generation']==c['compiled'][0]['generation']
    assert (HERE/'verify.py').read_bytes()==(HERE/'candidates/B/skills/meer-evidence/scripts/verify.py').read_bytes()
    assert bypass['direct_submit_without_relevant_check'] and not bypass['global_submission_gate']
    overhead=sum(e['wall_seconds'] for e in b['mechanism_evidence'])
    rows='\n'.join('|'+str(r['arm'])+'|'+str(r['HTTP_requests'])+'|'+str(r['charged_tools'])+'|'+f"{r['agent_wall_seconds']:.3f}"+'|'+str(r['native_resolved'])+'|'+str(r['cleanup_complete'])+'|' for r in records)
    write('CPU_VALIDATION.md',f'''# Actual CPU validation

Final Notebook {proof['Notebook_id']}/v1 COMPLETE. CPU_MODEL=SCRIPTED_ONLY; real Gemma requests0; research GPU0; formal Submission0.
Final payload SHA256 `{proof['payload_sha256']}`. Downloaded raw archive SHA256 `{proof['archive_sha256']}`, {proof['archive_bytes']}bytes, CRC valid.
audit.py independently verifies all {proof['source_members_verified']} extracted source members against frozen payload, candidate ZIP/member SHA, actual native TaskResult/JUnit and patch hashes, transports/Worker cleanup, official Compiler generation/schema consistency, actual skill verdicts, and corruption rejection. Raw path is private and recorded in CPU_ACCEPTANCE_CPU03.json.

| Owned session | Scripted HTTP requests | Official charged tools | Agent seconds | Native synthetic resolved | Cleanup |
|---|---:|---:|---:|---|---|
{rows}

All three candidates compile as actual single ADK LlmAgent with an initially empty skill state; actual Prompt is visible in outbound requests. All6original official tools execute. B/C have identical10declarations:6workspace tools+4organizer skill tools. The native Runner supplies its real sandbox code executor; no competitor callback/tool wrapper was injected. Generation16384/thinking4096/seed17 and300s/60/120 limits retained. Intended failed command returns a real tool error; execution continues to an owned207byte source repair, targeted assertion, explicit submit, native pytest/JUnit and cleanup.

12/12 real Linux adversarial tests pass, including POSIX timeout/descendant behavior. Three additional offline release tests pass: exact B/C single factor plus deterministic artifact rebuild, immutable writer rejection, and CRC-valid repacked source tamper rejection (LOCAL_RELEASE_TESTS.log). Local Windows run:11passed/1POSIXskip, not falsely counted as a Linux pass. Tests are engineering evidence, not model efficacy.

CPU01 140509598/v1 ERROR is preserved:12tests passed and EGR native resolved, but passive compile observer missed the Runner-local binding. CPU02 140510843/v1 COMPLETE proves A/B/C and mechanism behavior. CPU03 adds a real Runner bypass counterexample to the final payload. No frozen candidate changed between these CPU versions. Original UNKNOWN_STOP journals are retained with later independent read-only resource/source/version/output confirmation; no duplicate save.

Raw HTTP requests, owned patches, native logs/JUnit and any inherited private evidence stay outside Git. No real competition-task baseline or new model repair was run in this round. Scripted success does not predict Gemma compliance, repair rate, leaderboard score, or semantic correctness.
''')
    write('MECHANISM_TEST_RESULTS.md',f'''# Mechanism enforcement and adversarial evidence

Source: final actual CPU{proof['Notebook_id']}/v1,12Linux tests plus4native Runner sessions. The important distinction is local Skill enforcement versus global Agent behavior.

| Scenario | Observed mechanism behavior | Enforcement | EGR difference / limit |
|---|---|---|---|
| Repeated same source/check | B calls3times:CONTRADICTED,SUPPORTED,OBSERVED; child counts1,1,0 | Duplicate helper subprocess actually suppressed | EGR has no such verifier; C only returns UNKNOWN |
| Repeated search outside helper | B_BYPASS executes identical grep twice, unchanged results | NONE | Same bypass is possible in EGR; no global search controller |
| Success declaration without evidence | Scripted B_BYPASS declares success; Runner nudges then continues | Helper never accepts text as evidence; global declaration NOT intercepted | Do not claim hard success/termination control |
| Green before edit, failure after edit | Actual Python source edit changes hash; next helper runs and CONTRADICTS | Old receipt not accepted for current tree | Cannot stop Agent quoting an old result without invoking helper |
| Test has no evaluated assertion | print-only,assertTrue,ifFalse assert and unused test function all UNKNOWN | No SUPPORTED from exit0 alone | Structurally nonconstant expression can still be a semantic tautology |
| Initial repair/check fails | Real local assertion failure is CONTRADICTED; corrected source then SUPPORTED | Actual child execution/hash observation, not model JSON | Does not invent a correct fix |
| Diagnostic has no new information | Identical check/tree skips actual rerun, new_evidence=false | Only inside opt-in check | Arbitrary diagnostics remain allowed |
| Direct submit without relevant verification | B_BYPASS emits successful official submit, no helper or targeted test | NONE; actual bypass positively demonstrated | Native owned fixture later passes because scripted edit was correct; not pre-submit proof |
| Verification exceeds local budget | Hanging child times out, becomes UNKNOWN, process group killed | Max15s helper bound; native executor also limits global remaining time | No separate controller reserves future edit/submit time |
| Missing dependency / exception | Real ImportError check contradicts local success claim; classification retained as exception_type | Not promoted to support | Not proof the target Issue is unsolved or Agent algorithm failed |
| Source changes during check | Before/after hash mismatch -> UNKNOWN | Fresh evidence invalidated | Does not make untrusted workspace code tamper-proof |

Supported statement: this particular selected assertion script executed successfully on this observed unchanged tree. Semantic correctness, Issue coverage and Native Resolved remain UNKNOWN inside the helper. Tests of state flags alone are not used to establish global enforcement; B_BYPASS provides the explicit real counterexample.
''')
    write('BUDGET_ANALYSIS.md',f'''# Measured costs and limits

These are CPU engineering measurements on an owned6file tree, not Gemma benchmark estimates. Scripted tokens/usage are artificial and excluded from model-efficacy/cost conclusions. Real Gemma token use and added inference cost: NOT_MEASURED.

| Arm | Scripted HTTP requests | Official charged tools | Agent seconds | Synthetic resolved | Cleanup |
|---|---:|---:|---:|---|---|
{rows}

Columns above:arm, scripted HTTP requests, native charged tools, Agent seconds, synthetic resolved, cleanup. Detailed Worker times are in CPU_ACCEPTANCE_CPU03.json. B performs2actual assertion subprocesses plus1duplicate skip; total local helper wall time {overhead:.6f}s. B versus matched C Agent-time difference {b['agent_wall_seconds']-c['agent_wall_seconds']:.6f}s is one sequential CPU observation, not a reliable speed estimate. Native Skill transport/materialization also costs time and is included in Agent/Worker duration. The mechanism makes no model calls internally, but calling/loading it creates model turns/tool calls: actual counts above, not zero-overhead.

Frozen candidate budgets:300sAgent,60official charged calls,120scommand;32768context,16384output,4096thinking,seed17. Safety1024 belongs to a common research Context Guard, not a field magically enforced by candidate YAML. Future GPU uses an identical pinned guard for all arms. The organizer's default session budget is60minutes/100tools, while this candidate explicitly selects5minutes/60/120; these are experiment choices, not universal competition ceilings. Official context/size/allowed-model limits are independently documented.

The helper bounds one check to15s and hashes at most30000files/64MiB; source budget/timeout/unavailable evidence becomes UNKNOWN. No auto-expansion, dependency install, additional model, or verification loop is added. Several15schecks could still waste a substantial fraction of300s: cap is protection, not proof of optimal resource allocation. Repository-scale hashing overhead, live tool-context tokens, Gemma skill uptake and inference latency need the matched GPU experiment. Native charged skill calls count as observed; no custom counting or budget bypass is installed.
''')
    final=f'''# Final decision: GPU_READY_NOT_AUTHORIZED

Gate1 PINNED_INTERFACE_COMPLIANT: actual official guide/compiler/native skill executor support the chosen sandbox script. Unseen live private-scoring policy is not asserted; current public rule web body was unavailable.
Gate2 ENGINEERING_PASS: final Kaggle CPU{proof['Notebook_id']}/v1 COMPLETE from exact sealed/extracted payload;12adversarial tests,real Compiler/ADK/Runner/six tools+Skill,owned source edit,submit,native TaskResult/JUnit and cleanup verified.
Gate3 SCOPED_MECHANISM_PASS: real deterministic assertion execution/freshness/duplicate suppression changes behavior inside the Skill. GLOBAL_CONTROLLER_NOT_IMPLEMENTED: a real bypass session repeats searches, declares success and submits without relevant verification. No host callback or hidden tool interception is claimed.
Gate4 NOT_RUN:0realGemma/0GPU/0formalSubmission in this task. No repair-success advantage demonstrated.

Candidate A EGR `{lock['arms']['A']['ZIP_sha256']}`.
Candidate B MEER `{lock['arms']['B']['ZIP_sha256']}`.
Candidate C matched Prompt-only `{lock['arms']['C']['ZIP_sha256']}`.
Final payload `{proof['payload_sha256']}`; private raw `{proof['archive_sha256']}`.

1. EGR offers instructions but cannot independently reject weak/stale test evidence or suppress identical checks. Historical12sessions/315actions were actually re-read as hypothesis evidence.
2. MEER adds one actual official Skill script: local subprocess assertions,hash-bound results,conservative verdicts,small cache and bounded process lifecycle.
3. Verdicts come from process/file observations,not a model-declared JSON state or another Prompt paragraph.
4. Only the officially supported subset is implemented. Arbitrary custom Agent/host callback/tool wrappers are excluded.
5. It influences normal execution when called and returns observed evidence to the model; it cannot force its own use or override official six tools.
6. Enforced:helper assertion-count/freshness/verdict/time/cache policy. Advisory:Issue relevance,repair hypothesis,when to edit/submit. B_BYPASS proves global non-enforcement.
7. Local helper total{overhead:.6f}s on this fixture,plus visible model/tool invocation overhead. Actual Gemma token/latency cost unknown; full small-CPU numbers are in BUDGET_ANALYSIS.md.
8. Actual Linux12/12tests pass,three matched owned end-to-end sessions plusone real bypasscounterexample. CPU01ERROR retained,CPU02PASSretained,CPU03finalPASSverified.
9. No real-Gemma evidence of MEER improvement. Scripted native true is engineering only.
10. Candidate is ready for an authorization review for a controlled experiment,not automatic execution. GPU_EXPERIMENT_LOCK.json fixes sixA/B/Csessions on two previously CPU-admitted prospective tasks; final GPU worker/guard binding,intervening exposure,live resources/weights and separate authorization remain mandatory.
11. Largest remaining failure mode:the model bypasses the optional helper or chooses a wrong/tautological assertion; trusted semantic relevance cannot be inferred from a local pass. Untrusted scratch state is not an attestation boundary.
12. Do not replace EGR or any formal submission. First measure matched Native Resolved and all failure-inclusive costs; honor a negative result.

The branch changes only meer/v01/. Historical candidates,TaskResults,Verifier,official tool schemas,prior UNKNOWN and current official EGR submission remain unchanged. Exactly3unique CPU SaveKernel dispatches;CPU01runs1owned session before observer assertion,CPU02runs3,CPU03runs4.0researchGPU,0realGemma,0CompetitionSubmission. A sandbox preflight failure sent0requests. Raw evidence remains private;public artifacts contain code,hashes and derived metrics only.
'''
    write('FINAL_DECISION.md',final)
    archives=[]
    for attempt in ('cpu01','cpu02','cpu03'):
        root=ROOT.parent/('private-evidence/meer_v01_'+attempt)
        for manifest in root.glob('read-*/evidence_confirmed/OUTPUT_MANIFEST.json'):
            m=json.loads(manifest.read_bytes())
            for entry in m['files']:
                if not entry['file'].endswith('.zip'):continue
                path=manifest.parent/'output'/entry['file'];raw=path.read_bytes()
                assert sha(raw)==entry['sha256'] and len(raw)==entry['bytes']
                with zipfile.ZipFile(io.BytesIO(raw)) as z:assert z.testzip() is None
                archives.append(dict(attempt=attempt,path=str(path.resolve()),sha256=sha(raw),bytes=len(raw),CRC_valid=True,
                                     Notebook_id=entry['Notebook_id'],version=1,status=m['status']))
    partials=[]
    for root in (ROOT.parent/'private-evidence').glob('meer_v01_cpu*'):
        for ledger in root.glob('read-*/evidence_confirmed/READONLY_QUERY_LEDGER.json'):
            v=json.loads(ledger.read_bytes())
            if not v.get('stop_exception_class'):continue
            incomplete=[]
            for f in (ledger.parent/'output').glob('*.zip'):
                incomplete.append(dict(path=str(f.resolve()),sha256=sha(f.read_bytes()),bytes=f.stat().st_size,complete=False))
            partials.append(dict(read=str(ledger.parent.resolve()),exception_type=v['stop_exception_class'],partial_outputs=incomplete,SaveKernel=0))
    write('RAW_ARCHIVES.json',json.dumps(dict(raw_contents_public=False,archives=archives,read_failures_preserved=partials),indent=2)+'\n')
    # Exact bytes retained, including CRLF transport receipts. No raw HTTP/auth
    # bodies, signed links or evaluation test text may enter new public files.
    files={}
    for path in HERE.rglob('*'):
        if not path.is_file() or '__pycache__' in path.parts or path.name in ('AUTH_STATUS.json','INTEGRITY_MANIFEST.json'):
            continue
        data=path.read_bytes()
        if path.suffix in ('.py','.md','.json'):
            text=data.decode('utf-8-sig')
            assert not re.search(r'KGAT_[A-Za-z0-9_.-]+|X-Goog-Signature=[0-9A-Fa-f]{16,}|"Authorization"\s*:',text),str(path)
        files[path.relative_to(HERE).as_posix()]=sha(data)
    write('INTEGRITY_MANIFEST.json',json.dumps(dict(files=files,history_sha256=sha((HERE/'HISTORY_INTEGRITY.json').read_bytes()),
        current_frozen_candidates_verified=True,publication_secret_scan=True),indent=2)+'\n')
    print(json.dumps(dict(status='GPU_READY_NOT_AUTHORIZED',files=len(files),Notebook=proof['Notebook_id'])))


if __name__=='__main__':
    import io
    release()
