# Structured Verifier and one complete real E3 pair

**A complete, auditable pair was obtained. Neither arm resolved rich_3130.**
Both actual native Phase2 runs report **4passed,2failed,0errors**, exit1,
resolved=false. The corrected classifier retains these ordinary assertion
failures and continues from Control to E3. Batch infrastructure admission passes,
with no STOP and no not_run arm. This is not a new Kaggle leaderboard submission.

The current frozen E3 does **not** show a repair or time-to-repair advantage in
this pair. It reads less, but its first stable repair is33.468s later and it
introduces then corrects an initialization bug. Both exhaust300s without an
explicit submit. **No-Go for replacing S0 or automatically expanding to a
large confirmation experiment.** This one control-first task does not establish
that E3 is generally ineffective.

## Registration, execution and infrastructure

Study s1-e3-structured-smoke-04 uses independent s1-verifier-0.3.0; parent25c2954.
Preregistration and accepted CPU evidence were pushed in4620085 before GPU
Notebook version1 dispatch. Protocol SHA256:
`5d8c9c46e9736b2f4128fdf74047752fd8134cf8b82817c144cf287e5193e4e3`.
Kernel: wudangdexiaodoashi/gemma4-s1-e3-struct04-gpu, COMPLETE.

The predeclared minimum salted-SHA rule selected rich_3130 from43 previously
unmentioned Rich tasks; the full ranking, exclusions and rule hash are retained.
No reference repair was inspected. Base720800e6930d85ad027b1e9bd0cbb96b5e994ce3,
Issue452bde079727e28fb510b51d360e3db7a652977f698f6e74a648ce1e2404c16c,
snapshot208ec211fdb8819f192660f95d8476ffb43e4de5c068facc7430664306738536.
There was no task replacement, hotfix, retry or trajectory reuse.

Official Linux CPU02 actually passed113/113, including existing100 and13 new
native-Pytest/capture/production-audit-path regressions. CPU01 and CPU02 remain
separate preparations; only CPU02 admits this exact GPU source payload. See
CPU_VALIDATION.md for A–G and the metadata-only count correction.

On CPU and again on the GPU host, the clean unrepaired native baseline actually
ran all6 evaluator tests:1pass,5assertion failures,0errors. Native XML was
persisted before cleanup. This is not a model outcome. The expected bug is
markdown table text overwritten across styled fragments; evaluators and baseline
findings were not supplied to either Agent.

Real31B QATv2 on4L4/TP4 passed model-file checks, route/health/READY generation,
tokenizer/usage equality (16input+2output), and oversize admission rejection.
All134 runtime files,8 model files,41 model wheels and124 task wheels match
registration. Both arms use300s/60tools,command120s,output16384,thinking4096,
seed17,context32768/safety1024,six tools and one native ADK Agent. Sampling and
include_thoughts remain omitted as frozen. The only candidate factor is Prompt.
Control and E3 use independent clean Agent and evaluator sandboxes.

## Real tool/action comparison

Times below use actual successful tool responses after native Agent start.
An initial diagnostic edit is distinguished from a repair and from a repair
that survives its own runtime check. Full44-event timelines and returned
content are in analysis/*-timeline.md and *-tools.json; annotations and the
offline reproduction script are retained alongside comparison.json.

| Observable | Control | E3 |
|---|---:|---:|
| First target class read |9.635s,tool2|12.339s,tool4|
| First faulty on_text implementation read |13.743s,tool4|12.339s,tool4|
| First production diagnostic mutation |none|78.643s,debug print only|
| First repair edit |165.701s,tool23|178.434s,tool28;initially broken|
| First stable repair edit |165.701s|199.169s,tool31|
| Tools before first repair |22|27|
| Total native LLM/tool events |44/44|44/44|
| Successful read_file calls |17|11 plus1 invalid read|
| Exact repeated read arguments |2|0|
| Intersecting same-file read ranges |8|4|
| Tool error responses |8|6|
| Existing pytest executions on changed source |4|1 plus1 new narrow test|
| Explicit submit_patch |0|0|
| Native fallback Patch |1306bytes,applied|1259bytes,applied|
| Native Phase2 |4pass,2fail,0error|4pass,2fail,0error|
| Official resolved |false|false|
| Agent/worker seconds |300.010/329.691|299.999/329.162|
| Received-response input/output Tokens |237790/9296|252778/10054|
| Received-response total Tokens |247086,partial|262832,partial|

Range intersections include legitimate post-edit inspection and are not all
waste. Failed test commands are genuine negative evidence, not all invalid
tools. More detailed distinctions follow; raw timing/edit labels are never
converted directly into correctness claims.

Control tools1–10 locate the handler and TextElement precedent, with one
irrelevant range220–230 and later repeated class searches. Tool12 (81.699s)
really shows truncated table output, but the reproducer then raises because
Console.export does not exist. The single repair,tool23, initializes a Text
accumulator and appends fragments with current style. Tool24 (167.441s) displays
restored table text in the changed workspace but repeats the same export error.
Tool25 uses a nonexistent test path. Tools27–29 run the identical existing
test command three times without any intervening production change;tool31
reruns one file verbosely. Tools33–44 resume class searches/reads with no
further repair. No submit and no cleanup of repro.py follow.

E3 tools3–6 read the enclosing table/handler and TextElement. Its early probes
9,11,13 have **no markdown table separator**, so they render literal pipe text
and never exercise TableDataElement. Exit0 is not bug verification. Tool12
adds a debug print. Tool13 has no debug output;tools14–15 add a real header
separator and finally show repeated handler calls with only the last fragment
retained (88.343s). This is an actual probe change after observable evidence,
not a self-reported decision field. E3 subsequently spends tools16–27 on an
out-of-bounds read, repeated handler/context inspection and unsuccessful greps.

Tool28 initializes Text(justify=self.justify) **before assigning self.justify**;
tool29 installs the append implementation and removes the debug print. Tool30
really executes the modified handler and raises AttributeError at line333
(192.936s). Tool31 fixes the assignment order at199.169s;tool32 then renders
the complete styled table at226.969s. This is clear counterevidence followed
by a real corrective edit, but the bug and its correction consume budget.
Tool41 checks ANSI-rendered output,tool42 adds a weak substring test,tool43
runs the existing file and sees failures,tool44 passes only the new narrow test.
There is no subsequent production repair or explicit submission before cutoff.

## Correctness, old behavior and provenance

The original six evaluator cases are unchanged. Both arms turn the same three
baseline failures into passes:test_markdown_table,test_inline_styles_in_table,
test_inline_styles_with_justification. test_partial_table stays passing.
test_markdown_render and test_inline_code remain failing;their JUnit failure
messages are exactly equal to the clean baseline, including ANSI/color
differences. These two failures therefore cannot be called newly introduced
Agent regressions. Their deeper dependency/version cause is not established
here. They remain official failures;no tests,environment,expected output or
verdict were changed to remove this endpoint limitation.

During the Agent, Control actually sees3fail1pass in test_markdown.py and an
additional failing no-hyperlinks file;E3 sees3fail2pass after adding its test.
The Agent workspace initially lacks the evaluator's independent test overlay,
so these are different observations from the final native six-case Phase2.
Do not replace Phase2 with either Agent test invocation. The new E3 substring
test cannot establish exact style/link/justification correctness by itself.
Native protected-file filtering excludes its test edit and test_output.py from
the submitted fallback Patch. Both final Patches retain one reproducer;E3's
debug print is removed. No reference answer or evaluator test was edited.

Both Patches apply and improve the tested table behavior;neither is a complete
official repair. E3's first repair temporarily breaks the table constructor.
No additional failure appears among the six final evaluator cases, but this
does not prove preservation of all untested behavior. Control's plain-fragment
conversion and E3's direct Text append have different possible untested scope;
no extra success or failure is asserted from inspection alone.

Passive import records include sys.path,executable,__file__,realpath,source SHA
and module-code execution. Matched ADK command windows prove changed
rich.markdown actually executes for Control tools24/27/28/29/31 and E3
tools30/32/41/43/44. Actual changed source hashes match native evaluator
workspace bytes. These are stronger than exit0 but are not function-coverage
proof. The real output/tracebacks and tests separately establish behavior.
See source_provenance.json for command IDs and raw evidence filenames.

## Structured Phase2 and cleanup evidence

Official swegemma0.2.11 verification.py::verify_task already requests
--junitxml. The isolated manager reads that exact tmp file after the unchanged
native command returns and again immediately before native stop. Original
stdout/stderr,TaskResult,XML,command hash,capture timing and source hashes are
saved for both failures;no alternative test run replaces native Phase2.
XML/count/exit/stdout consistency classifies assertion_failure with no infra
stop. A local read-only replay through the same production audit recomputes
identical structured results. Failed XML survives both sandbox removals.

JUnit SHA256 Control:
00976a51e2b1d04d18bb7f5df8c0d77657b594a6ebf3fe0e4ee126d5e6530c38.
E3:719d70e6093fab3943b7defe3237d986eb7f3634560efff745fa72de8137f136.
Native pytest wall duration is1.922/1.919s, excluding sandbox preparation.
Each worker proves cleanup_complete with no remaining sandbox directory.

Each arm dispatches48 HTTP requests:47 real responses and1 real CancelledError,
all48 with correlated IDs and known terminals. There are45 six-tool requests
(44 answered,one cancelled) and3 no-tool history-compaction requests. Native
LLM/tool counters are44,not48;both counters and raw requests are retained.
Cancellation occurs0.00727s/0.00609s before native Agent end and propagates.
The unreceived request's usage remains null;both Token totals are partial.

Server gauges independently report zero running/waiting at10.860/11.872/12.884s
after Control cancel and10.635/11.647/12.660s after E3 cancel, before proceeding.
Actual backend log bytes are exported this time (66070bytes,SHA
1473cb00b099d4133da4a734900fb9933667f289c38f3f0d9bc4e6c4fd20cdff).
They do **not** provide a request-specific abort acknowledgement;the server
abort counter is0. We claim reported idle at observation times,not immediate
backend cancellation or recovered usage. All7 observed server PIDs terminate
without forced kills. This meets the preregistered reclamation gate.

E3 uses15746 more observed response Tokens (+6.37%);this is not a complete-cost
delta because both cancelled responses lack usage. Raw official token/cost
zeros are retained but are not true zero cost. Maximum completed input/output
is8613/1077 for Control and9166/909 for E3;no observed length finish. Platform
log ends at1357.755s,about22.63min or1.509L4-hours as a4-device allocation proxy,
not billing or pure inference time. Server installation/startup is shared.

## Integrity and decision

GPU raw SHA256:
`a5e062da220fb9c0b0912006c5c1a82e3a7fd98eb75048614379cd0dfe07a2d5`.
CRC and514 outer manifest entries plus134/139 nested run entries verify.
Raw ZIP,all native traces,ADK/tool events,Patch,XML,HTTP lifecycle,backend log,
import provenance and process/server observations are retained. The first
download lost its connection after the complete main archive;read-only log
retrieval succeeded separately. No GPU rerun occurred. Delivery and source
audits are recorded separately;historical STOPs remain byte-identical.
All2478 parent files,945 shared original files and8 CURE archives are unchanged.
All134 actual CPU/GPU source files match each other and registration. The
unused V1 Prompt has a preexisting local CRLF checkout versus the archived LF
payload;it was not edited or executed. Its old local byte hash remains intact,
and both actual payloads use the same pinned LF bytes. The other133 local
source files also match the execution bytes;both executed candidate members
and ZIPs match exactly. This distinction is retained in the integrity audit.

A. E3 changed the observed action sequence, but two stochastic single-task
trajectories do not isolate which specific Prompt sentence caused each change.
B. Fewer reads/overlaps are a limited positive observation,offset by invalid
non-table probes,more mutations and later stable repair.
C. Its premature init edit is demonstrably wrong and corrected after a real
traceback. Early editing alone is not success.
D. Both run real old-behavior tests;E3 eventually validates a narrow new test,
but neither resolves remaining failures,cleans all diagnostics or submits.
E. **No-Go for promoting E3 or automatically running a multi-task expansion.**
Repair endpoints tie,stable repair is later,and partial Token use is higher.

The lowest-cost next work is read-only attribution of the two preexisting
golden-color failures against official pinned dependencies,without changing
this experiment or its official results. It is not yet a proven environment
root cause. For a future candidate, first test one explicit anti-repeat/probe
validity mechanism on CPU;any Prompt change needs a new candidate and separate
registration. If unchanged E3 is independently confirmed later,use fresh tasks,
balanced run order and retain failures,not selected successes. No further GPU
run is launched here. S0 Public0.13/submission57261002 remains the only confirmed
leaderboard score;no LoRA,other factor or formal submission was started.
