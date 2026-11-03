"""Publish evidence-bound recovery reports; never relabel old CPU receipts."""
import hashlib,json,sys
from datetime import datetime,timezone
from pathlib import Path
from forensic import autopsy
R=Path(__file__).resolve().parent;D=R.parent;ROOT=D.parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
load=lambda p:json.loads(Path(p).read_bytes())
def dump(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n',encoding='utf8')
def doc(name,body):(D/name).write_text(body+context,encoding='utf8')
facts=autopsy();dump(R/'AUTOPSY.json',facts)
assert all(facts[k] for k in ['native_hash_matches_receipts','session_hash_matches_done','cleanup_hash_matches_done','archive_matches_extracted_evidence'])
protected=load(R/'HISTORICAL_BEFORE.json')['files']
drift=[p for p,h in protected.items() if not Path(p).is_file() or sha(p)!=h]
before=load(R/'V02_BEFORE.json')
changed=[p for p,h in before.items() if not (D/p).is_file() or sha(D/p)!=h]
assert not drift
assert set(changed)<=set(['result_contract.py','FINAL_REPORT.md']),changed
dump(R/'HISTORICAL_AFTER.json',dict(observed_at_utc=datetime.now(timezone.utc).isoformat(),count=len(protected),all_match=True,changed_protected_files=drift,changed_previous_V02_files=changed,CPU01=load(R/'ARCHIVE_INTEGRITY.json')['01'],CPU02=load(R/'ARCHIVE_INTEGRITY.json')['02']))
from result_contract import native_execution_check
trust=native_execution_check(D/'cpu02-evidence/worker/trusted/NATIVE_RESULT.json')
dump(D/'NATIVE_TRUST_AUDIT.json',dict(status='BLOCKED_INFRASTRUCTURE',audit_type='Independent re-audit of original CPU02; not a new Native run',observed_at_utc=datetime.now(timezone.utc).isoformat(),trust_passed=False,raw_Native_resolved=False,raw_pytest_exit_code=1,hash_matches_session_and_done_receipts=facts['native_hash_matches_receipts'],session_hash_matches_done=facts['session_hash_matches_done'],cleanup_hash_matches_done=facts['cleanup_hash_matches_done'],complete_archive_matches_extracted_evidence=facts['archive_matches_extracted_evidence'],integrity=trust,cleanup=facts['cleanup'],source_binding=facts['source_binding'],historical_300_unchanged=True,new_Linux_acceptance='NOT_RUN',GPU_dispatch='NOT_RUN',reason='187 provider-resolution errors plus4 confirmed network-confinement failures'))
plan=load(D/'SMOKE_TASK_LOCK.json')['tasks'][0]
context=f'''
## Evidence identity and execution boundary

Generated UTC: {datetime.now(timezone.utc).isoformat()}. Audited PR46 source commit: `9ef032ab23335cb5a09c4937d7962205f5962f79`.

Task `{plan['instance_id']}`, base `{plan['base_commit']}`, Issue SHA256 `{plan['issue_sha256']}`, snapshot SHA256 `{plan['official_snapshot_sha256']}`. Package B SHA256 `{load(D/'PACKAGE_MANIFEST.json')['arms']['B']['sha256']}`. Official evaluator swegemma0.2.11 source SHA256 `{load(D/'evidence/EVALUATOR_IDENTITY.json')['sha256']}`; unchanged.

Original CPU02 archive: `cpu02-output/egrd-v02-cpu-hardening02.zip`, SHA256 `25b2a360c62023c48617fe8c3bb8734d4230a2d3668eccc33cb4e22f20fcf25a`. Raw records: `cpu02-evidence/worker/trusted/NATIVE_RESULT.json`, `native-junit-0.xml`, `NATIVE_COMMANDS.json`; Agent/Native cleanup receipts and original session/done hashes retained. Full191 failure/error case identities, trace hashes and excerpts: `native-recovery/AUTOPSY.json`.

Commands/timestamps/exit codes: `native-recovery/REGRESSION_EXECUTIONS.json`, `FOLLOWUP_EXECUTIONS.json` and referenced logs. Actual prior Native pytest command is recorded verbatim in AUTOPSY.json; exit1. Prior worker stage exit0 did not imply trustworthy test execution. New CPU SaveKernel0, GPU SaveKernel0, Gemma requests0, packages installed0. Local tests validate classification/source evidence; they do not replace Native evaluation. New Linux service acceptance and Native revalidation are NOT_RUN.
'''
doc('REQUESTS_FAILURE_AUTOPSY.md','''# Requests failure autopsy

Status: BLOCKED_INFRASTRUCTURE. The complete CPU02 archive passes CRC and recorded SHA checks. All324 JUnit cases were inspected, including every error and ordinary failure tag.

| Group | Count | Confirmed cause | Original evidence | Compliant action |
|---|---:|---|---|---|
| HTTP fixture resolution |183|Requests tests/conftest.py:25 defines httpbin(httpbin), but no upstream fixture definition resolves; available fixtures show the wrapper only|Every matching raw JUnit error chain; AUTOPSY records each case/index/trace SHA|An approved registered provider and its dependencies would be necessary; none supplied in the59 actual wheels|
| HTTPS fixture resolution |4|tests/conftest.py:30 defines httpbin_secure(httpbin_secure), with the same missing upstream provider class|All4 distinct secure-fixture chains|Same provider prerequisite; no TLS startup occurred|
| Network confinement, encoded as failure |4|Socket creation itself raises EACCES before connect; urllib3 wraps it as NewConnectionError and Requests ConnectionError instead of the expected ConnectTimeout|test_connect_timeout[timeout0/1], test_total_timeout_connect[timeout0/1]; socket.py:232 and urllib3/util/connection.py:64|Existing confinement cannot support these unchanged tests; do not suppress or reinterpret them as repair failure|

There are at least two independent capability defects: provider resolution and real network capability. The187 errors share a fixture-provider failure mechanism; the other4 failures are independently observed network denial. Installing a provider alone cannot establish acceptance.

The locked source requires pytest-httpbin==2.0.0, httpbin~=0.10.0 and trustme. Supplied wheels contain pytest8.4.2 but no pytest-httpbin or httpbin. The installed distribution version was not directly probed in CPU02, so it remains UNKNOWN; absence of a registered usable provider is confirmed. Repository dev requirements constrain pytest<=6.2.5; compatibility with8.4.2 is an additional UNVERIFIED risk, not the observed cause of all errors. Official subprocess setup skips install_test_dependencies for the manager class; this adapter depends on its explicitly supplied wheel set. No automatic dependency provisioning repaired that omission.

Read-only [PyPI2.0.0 release metadata](https://pypi.org/pypi/pytest-httpbin/2.0.0/json) and SHA-verified released source were audited without installing or importing it. The plugin registers both fixtures via pytest11, starts WSGI servers on127.0.0.1 with port0 by default, and uses a thread with context-manager shutdown/join. SecureServer uses bundled certificate/key material and SSLContext. Provenance: PROVIDER_SOURCE_PROVENANCE.json. Actual HTTP/HTTPS startup, bind conflict, TLS handshake, CA validation and fixture-thread teardown remain NOT_RUN because fixture resolution failed first.

The inherited launcher constructs a clean environment: no host HTTP_PROXY/HTTPS_PROXY/ALL_PROXY/NO_PROXY values are inherited. Native uses the same launcher and exact59-wheel list as Agent. The shared source prefix is /workspace/src:/workspace:/opt/approved; Agent import receipt and Native src/requests trace confirm source binding. Full cross-workspace byte-fingerprint parity was not captured and is UNKNOWN. Native before/after source guard is unchanged.

Policy and runtime corroborate each other: inherited seccomp denies connect and AF_INET/AF_INET6 socket creation; the actual CPU02 isolation probe reports NETWORK_DENIED, and all4 failure traces show AF_INET SOCK_STREAM construction rejected with errno13. DNS, proxies, certificate expiration and port collision are not established causes of the187 setup failures. Numeric10.255.255.1 timeout cases cannot acquire their required socket behavior under the current policy.
''')
doc('REQUESTS_FIX_DESIGN.md','''# Requests environment fix decision

Decision: NO_COMPLIANT_ENVIRONMENT_REPAIR_AVAILABLE under the present constraints. Stop at PhaseB; do not dispatch another CPU acceptance run or GPU job with a known-incompatible environment.

Prerequisites are an approved registered pytest-httpbin2.0.0/httpbin dependency closure, an auditable confinement-compatible real local HTTP/HTTPS service, and legitimate socket/timeout behavior for the four unchanged timeout tests. Current confinement forbids the socket capability itself. This task prohibits weakening it and prohibits unapproved package installation.

No fake httpbin fixture, test skip/xfail, deselection, mocked timeout, external web service, TLS-verification bypass, syscall relaxation, host socket mount or substitute evaluator is introduced. A future separately approved runtime/dependency solution would need engineering and real Linux validation; it is not claimed implemented here. Supporting only loopback would not by itself establish the numeric-address timeout tests' behavior.

The minimal compliant code change in this task is a stricter Native infrastructure classification: real socket EACCES wrapped as HTTPConnection/NewConnectionError is rejected even when pytest puts it in a failure tag. Ordinary behavioral assertion failures remain admissible. Setup-error cases are removed from the executed-body count, correcting322 to135. Neither change can promote a failed trust audit to PASS. Raw official resolved values and scoring code remain unchanged.
''')
doc('REQUESTS_FIX_IMPLEMENTATION.md','''# Implemented changes

Only result_contract.py runtime trust checks changed. No source-binding, package, model, prompt, official tool, official test, SDK evaluator or sandbox-network setting changed. No dependency was installed; released provider source was read as data only and is not on the runtime import path.

native_execution_check now identifies the conjunction HTTPConnection + NewConnectionError + [Errno13] Permission denied in original failure traces. Four actual CPU02 failure records are rejected in an owned classifier regression. Normal assertion failure and an unrelated errno string remain admissible. This is conservative research infrastructure gating, not scoring modification.

Executed testcase bodies now exclude both skipped and setup-error nodes:135 bodies versus324 collection records, including131 passes and4 failed bodies. The187 provider setup errors were never test-body executions.

New forensic code and tests are under native-recovery/. Compiler tests execute the unchanged sdk_acceptance logic against an isolated package copy, preserving historical compiler receipts. Current FINAL_REPORT replaces the landing report only; its exact prior bytes are preserved at native-recovery/previous/FINAL_REPORT.md. Existing CPU archives, raw results, historical reports and claims remain intact. Before/after hashes are recorded separately.

The initial fixture-evidence test run contained a label-format mismatch (NOT_RUN plus reason in one field). It was corrected to separate status and explanation; failure logs and the successful follow-up remain preserved. This did not change the acceptance gate or any official expectation.
''')
doc('REQUESTS_REGRESSION_REPORT.md','''# Regression results and limits

Read exact final exit codes in REGRESSION_EXECUTIONS.json and FOLLOWUP_EXECUTIONS.json. Required existing47, legacy27, infrastructure6 and four actual official Compiler package checks are rerun. New forensic/classifier suite has17 checks against original evidence, source binding and negative trust cases. These are CPU unit/process checks, not real fixture service acceptance.

| Requested capability | Actual coverage | Live service result |
|---|---|---|
| Requests source precedence |Existing source import subprocess test plus actual CPU02 Agent receipt/Native trace|Prior source binding observed; no new Linux run|
| Fixture provider availability / missing provider |All187 traces and59-wheel inventory checked|Provider resolution failed|
| HTTP startup |Exact failure-before-start evidence; provider source audited|NOT_RUN|
| HTTPS startup |Separate4 secure traces; TLS source audited|NOT_RUN|
| Fixture teardown |No invented teardown success; actual sandbox cleanup verified|NOT_RUN for fixture lifecycle|
| Port conflicts |No EADDRINUSE evidence; default port0/source reviewed|NOT_RUN|
| Proxy isolation |Explicit clean launcher environment checked|Source-verified; direct runtime env dump not available|
| Agent/Native parity |Same wheel hashes, shared command binding, source paths|Complete byte parity UNKNOWN|
| Abnormal fixture termination |No service was started; lifecycle not fabricated|NOT_RUN|
| Cleanup |Both original cleanup receipts checked; existing cleanup/process tests rerun|Original sandbox cleanup confirmed|

The gate for dispatch is not met: positive fixture service acceptance cannot be inferred from passing these forensic checks. Initial RED tests and the label-mismatch failure are retained, along with successful final reruns. No tests were deleted or weakened.
''')
doc('CPU_REVALIDATION_REPORT.md','''# Linux CPU revalidation decision

Status: BLOCKED_INFRASTRUCTURE. New immutable acceptance Notebook, SaveKernel and Native rerun: NOT_RUN.

PhaseD requires A-C acceptance. PhaseA proved missing usable fixture providers and a separately incompatible socket policy. PhaseB cannot provide a compliant environment repair without capabilities forbidden in this task. Positive HTTP/HTTPS lifecycle, port conflict and crash/teardown acceptance therefore remain NOT_RUN. Dispatching known-broken CPU03 would not establish trustworthy acceptance.

The original CPU02 Native result hash matches both SESSION_RESULT and worker_done. JUnit parses, has real executed bodies and confirmed sandbox cleanup. Nevertheless187 setup errors and4 network confinement failures reject trust. Raw CPU02 PASS and raw Native resolved=false are unchanged. The latest guard is used for this independent artifact re-audit, not as a replacement for the Native evaluator.

All300 historical protected hashes, CPU01/CPU02 archives, task/snapshot/model/package locks and official evaluator source are checked. No hidden answer, changed expected test or substitute task is used. No new Linux acceptance is claimed.
''')
doc('GPU_READINESS_FINAL.md','''# GPU readiness review: not entered

Status: BLOCKED_INFRASTRUCTURE. PhaseF is conditional on CPU_ACCEPTED, which was not reached. No GPU, model load, real Gemma request,31B fallback or competition submission occurred.

Existing GPU12_AUTHORIZATION is retained as historical permission; this recovery task explicitly prohibits GPU execution. Latest capacity/quota and four accessible L4 cards are NOT_CHECKED because the prerequisite failed; no historical capacity record is represented as current confirmation. The model/package/task identities remain frozen. Static budgets remain Agent300s, command120s,60 tools,80 turns and the existing archive/cleanup reserve; their preservation is not runtime readiness evidence.

Eligibility for the12B smoke: NO until an approved compatible fixture/runtime solution passes the unchanged full Native suite with zero infrastructure errors and confirmed source/cleanup integrity. Do not consume the future GPU one-shot claim.
''')
doc('FINAL_REPORT.md','''# EGRD V0.2 Native environment recovery

**Final status: BLOCKED_INFRASTRUCTURE.** Full autopsy is complete. There is no compliant environment repair under the current approved dependency set and unchanged socket confinement. No new Kaggle run, GPU or real model execution was performed.

## Required decisions

1. **183 httpbin errors:** OBSERVED recursive fixture resolution at Requests tests/conftest.py:25; the upstream plugin fixture is not available to pytest. Required provider2.0.0 is absent from the actual59 supplied wheels. Installed-distribution version beyond that inventory is UNKNOWN.
2. **4 httpbin_secure errors:** OBSERVED same missing upstream-provider mechanism at line30, before TLS initialization. A certificate defect is not established.
3. **One or multiple issues?** The187 setup errors share a provider-resolution cause. Additionally all4 ordinary failure tags are confirmed AF_INET creation EACCES, an independent security/runtime incompatibility, not repair failures. Potential pytest8.4.2 versus repo<=6.2.5 compatibility remains UNVERIFIED.
4. **Environment changes:** None. No package install, fixture replacement, network relaxation, service, prompt/model change or scoring change. Only research trust classification and executed-case accounting were strengthened.
5. **Official source binding:** OBSERVED /workspace/src import in Agent and matching Native source traceback/command; source guard unchanged during verification. Full pre-patch cross-workspace byte parity is UNKNOWN, not fabricated.
6. **All fixtures executed?** NO. Provider resolution failed; HTTP/HTTPS service lifecycle and TLS are NOT_RUN.
7. **Zero infrastructure errors?** NO. Original JUnit contains187 setup errors plus4 failed bodies caused by network confinement.
8. **Independent trust passed?** NO. Original hashes/cleanup pass, but execution integrity fails. The original CPU02 PASS receipt is preserved as historical plumbing evidence only.
9. **300 protected hashes unchanged?** YES, exact before/after comparison; CPU01/02 archive hashes and CRC are unchanged.
10. **Eligible for authorized12B smoke?** NO. Native infrastructure acceptance is still blocked, and this task forbids GPU dispatch.

## Engineering result

Real network-denial failures previously could look like ordinary assertion failures once fixture errors were removed. A failing regression using all4 original failure records demonstrated that gap; the strengthened guard now rejects them. Executed-body accounting is corrected from322 to135:131 pass bodies plus4 failed bodies, excluding187 setup errors and2 skip/xfail records. Official raw resolved remains false.

Existing CPU regressions and actual Compiler checks were rerun; see REQUESTS_REGRESSION_REPORT and exact command receipts. New17 checks are forensic/classifier tests, not fabricated positive HTTP/HTTPS acceptance. The old final report is preserved byte-for-byte under native-recovery/previous/.

## Exact blocker and next decision

An approved provider/dependency closure and a permitted isolated runtime capable of genuine HTTP/HTTPS sockets and the unchanged timeout tests are required. Current seccomp denies socket creation itself. Installing a package alone would not fix that. No compliant solution is claimed, and no restriction is weakened. Further Linux dispatch should wait for a separately approved runtime/dependency solution, rather than repeat a known-broken run or change the official suite.
''')
print(json.dumps(dict(status='BLOCKED_INFRASTRUCTURE',historical_unchanged=not drift,protected_count=len(protected),errors=trust['errors'],network_failures=trust['infrastructure_failure_cases'],executed_bodies=trust['executed'])))
