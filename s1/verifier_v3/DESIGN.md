# Structured Verifier research infrastructure0.3.0

This is an independent research version. No old runner,STOP,Prompt,candidate ZIP,
native scoring API or test content is edited. The original SDK Phase2 already
passes --junitxml but does not export the failing XML before stopping its sandbox.
The subclass reads that exact file after the unchanged native command returns and
again before native stop,using the documented subprocess tmp mapping. Raw bytes,
SHA,size,command hash,capture timing and original stdout/stderr are durable.
No extra Agent tool or verification rerun is introduced.

## Event classification

Original JUnit testcase failure/error/skipped nodes and counts are authoritative
test events. Error stage comes from actual error-node reporter metadata,not from
case names,source snippets or stdout words. Recognized categories are passed,
assertion_failure (test-call failure),setup_error (setup/teardown phase recorded),
collection_error,internal_error,verifier_execution_error and unknown_unparsed.
Counts must match suite aggregates and the native terminal statistics line plus
exit status. The parser reads only the final anchored statistics line; it never
scans arbitrary output for ERROR,ModuleNotFoundError or numbers followed by errors.

Exit0 needs actual passing cases,no failures/errors,consistent XML/summary,and
the unmodified official resolved result. Missing/damaged/unsafe/oversized XML,
unknown stages,multi-outcome testcases,count contradictions or unavailable native
execution fail closed. No JUnit success is synthesized from stdout. Unsupported
report shapes stop rather than silently relaxing the schema.

## Attribution is separate

An ordinary native assertion failure is a valid algorithm outcome and permits
the other arm if HTTP,context,trace,cleanup and other gates pass. A setup or
collection event is not automatically external environment. Verified clean-base
blocker plus matching call-chain evidence can support environment attribution;
otherwise it remains unknown pending causal evidence. A narrow parser-error
case can be attributed to Agent regression when the real JUnit root traceback
names a production file and its executed bytes differ from the verified clean
baseline. Generic import exceptions are not automatically blamed on either side.
Ambiguous attribution is an evidence gate failure,not confirmed Agent failure.

Native TaskResult, resolved,test_exit_code and Phase2 output remain untouched.
The independent audit replaces only the legacy verifier-normalization findings
that structured evidence resolves. A completely evaluated empty Patch is an
algorithm outcome,not an automatic infrastructure stop. All other old HTTP,
generation,Patch checkpoint,trace,isolation and cleanup gates remain active.

## Frozen historical replay

The old Rich and Requests archives did not retain failure XML. A separately
attested,read-only replay mode supports only nonzero native outcomes with final
Pytest counts and matching generated failure/error sections. It classifies
Rich4 failed/19 passed as assertion_failure and Requests194 setup errors using
the already verified clean provider/call-chain evidence. It cannot announce a
pass,qualify a new task,or replace required prospective JUnit. Historical bytes
and STOPs are never changed. This limitation is explicit in evidence_level.

## Evidence and runtime boundary

The new worker invokes the unchanged official single-Agent loop under the same
deadline/context/Patch observers. Import evidence now records all loaded modules
under the registered prefix,so an unknown new Rich submodule can be audited by
actual executed path and source hash. It remains passive provenance,not proof
of assertion coverage. Backend log files are copied only if the SDK exposes an
existing path; missing logs remain missing. Independent server metrics and
process-tree cleanup,not client cancellation alone,govern reclamation admission.

CPU tests run actual manager/Pytest/file-capture/audit paths and save native input
reports,including deliberately corrupted test copies and their original reports.
Controlled tests are infrastructure checks,not model repair tasks or scores.
