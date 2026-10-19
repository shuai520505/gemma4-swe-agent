# Label-masked tool-action audit

First-pass seal: `11067bf7259d1375d5602815af15b804f37f5c9aac71a6419607d0fe171f724c`. Labels, model narration and official outcomes were hidden until this JSON was saved. Same reviewer knew the study design; no independent blinding claim. X=Control, Y=EGV was revealed afterward. Full arguments/results, monotonic times and original ADK line numbers remain in [TOOL_TIMELINE.json](analysis/TOOL_TIMELINE.json) and the masked X/Y records. No self-described decision field is used as evidence.

Times below are seconds from each native Agent-loop start, not Notebook start. A check is counted per command. A legitimate failing test is not an invalid tool call.

| Arm/action; original ADK call→return line | Time | Validity | Provenance | Novelty | Consequence |
|---|---:|---|---|---|---|
| EGV19;37→38 | 152.139→154.266 | Three self-authored HTTP status/content assertions call app.frontend/router.frontend | Workspace FastAPI baseline bytes | Reveals absent interface | EGV20/21 implement it |
| EGV22;43→44 | 197.557→199.640 | Same checks execute new methods; 404 contradicts asserted200 | New applications/routing source SHA | Necessary post-edit check; discriminates incomplete static behavior | EGV23/24 change html=True |
| EGV25;49→50 | 236.120→238.160 | Same three assertions pass | Both corrected workspace files; new SHA | Necessary correction retest | Local path confidence gained; no broad old-behavior coverage |
| EGV27;53→54 | 282.431→284.457 | Same assertions pass | Same source/input/hypothesis evidence | Redundant after read-only action26; no documented confidence reason | No new discriminating result or submission |
| Control31;61→62 | 172.352→173.252 | Mount construction + printed hasattr; no frontend or HTTP request/assertion | Workspace FastAPI, pre-edit bytes | Initial evidence that inherited mount exists; only proximal to requirement | Later wraps mount; no target check |
| Control36;71→72 | 229.161→229.985 | Prints both hasattr values; never calls frontend | Same pre-edit workspace bytes | Duplicates capability evidence from31; no relevant changed condition | No new distinguishing evidence |

EGV's target-check executions: 4 total, 3 informative, 1 unchanged repeat. Control's target-check executions: 0; 2 non-target print-only probes, 1 of which repeats evidence. **EGV did not reduce the raw count of redundant behavioral checks** (1 each); it increased relevant asserted checks. Necessary retests after changed code are not counted as waste. A capability probe can be useful localization evidence while still being insufficient behavioral validation.

EGV22 provides the clearest counterevidence chain: missing html index behavior causes 404; both production edits add html=True; EGV25 passes without altering its tests. The first-pass audit predicted this local improvement before reading official outcomes. It does not establish SPA fallback, route precedence, missing static-file behavior, or complete API compatibility. None of those broader contracts was validated by these local checks.

Control43/47 are successful file edits, but introduce literal backslash-escaped triple quotes. There is no compile, import, HTTP test or pytest run afterward. Native Phase 2 later confirms the syntax error; that outcome was not needed to flag its missing verification in the first pass. Its `repro_mount.py` remains in native fallback Patch. EGV's self-authored `tests/test_frontend.py` is absent from native fallback Patch; the evidence does not prove the Agent deleted it, only that the official Patch filters omitted it. Do not infer a manual diagnostic cleanup that never occurred.

## Source and assertion confidence

Passive per-command startup/exit records save sys.path, actual module __file__/realpath and source hashes. For EGV19, applications/routing hashes match baseline. For EGV22 they match its initial methods; for25/27 they match html=True final methods. [PROBE_PROVENANCE.json](analysis/PROBE_PROVENANCE.json) joins each command to original records. HTTP assertion traces confirm target invocation; imports alone would not.

The passive aggregate `outside_workspace` also observes expected installed dependencies. FastAPI per-module entries are within_workspace=true and module_code_executed=true; those are the relevant source facts. Neither Agent itself checked a module path or asserted a source-version identity. Thus researcher-confirmed provenance is stronger than the model's observable provenance reasoning.

Existing old-behavior regression runs: **zero for both**. The final EGV official output includes precedence/partial-match failures, so passing its three happy paths cannot establish preservation. Native evaluator findings were read only after the first-pass seal and were never passed back to Agents.

## Investigation, editing and submission

EGV19 follows 17 investigative tools + one test-file write. Its first production edit is action20, returned at160.085s; 19 tools precede it. Both final methods are revised by234.755s; local checks finish at238.160s. There is no stable whole-task repair time.

Control first production edit is43 at268.316s; 42 tools precede it. Its earlier action30 at171.188s only writes a diagnostic script. The automatic `first_edit_action_seconds` field counts this diagnostic write (and EGV's test-file write), so it must not be reported as first production repair.

Exact repeated read_file requests: EGV0, Control3. Control repeats applications41–100, routing1723 default read, and staticfiles whole file. Repeated class-location greps and overlapping ranges add investigation redundancy. EGV has overlapping ranges too (e.g. routing2540–2570 and2560–2575); exact-repeat counts are not exhaustive information-waste estimates. Source reads after edits can be useful review and are not automatically waste.

Neither arm has malformed tool schema calls. Several grep no-match returns are real searches, not environment errors; Control also executes empty-output grep pipelines that do not locate a useful method boundary. Both arms lack a final git diff inspection and explicit submit_patch. Native fallback preserved both Patches before separate Phase 2 and cleanup.

This single fixed-order, single-seed public task supports a behavioral difference. It cannot separate Prompt causation from trajectory variability/order effects or estimate a general repair-rate advantage.
