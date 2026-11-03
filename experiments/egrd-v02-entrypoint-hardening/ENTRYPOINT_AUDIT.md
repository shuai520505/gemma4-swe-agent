# Official entrypoint audit

Evidence classes: CPU_VERIFIED for compiler/tests; STATIC_ANALYSIS for SDK source inspection; REAL_GPU_OBSERVATION only for preserved V0.1 history. V0.2 real-model execution is NOT_RUN.

The four real official compilations register one ADK agent and exactly the six original workspace tools, plus official SkillToolset accessors. See evidence/SDK_COMPILER.json and SDK_TOOL_SCHEMAS.json.

Verified accessor schemas:

```text
load_skill(skill_name="egrd-repair")
run_skill_script(skill_name="egrd-repair", file_path="scripts/egrd.py",
                 args={"request":"<JSON string>"})
```

run_skill_script also supports an argv array; the frozen prompt uses the verified long-option object form. Required parameters are skill_name and file_path. The init JSON retains issue_id, original, model_id, requirements and all six claim-list fields. Unknown facts carry UNVERIFIED. Exact original Issue SHA is checked against actual initialization output and exported state. The official agent task text does not expose canonical Task ID or necessarily the model alias; explicit UNVERIFIED placeholders are permitted while host records the exact identity.

All packages prepend load -> successful return -> init -> successful schema/hash/phase check before exploration. At most one corrective additional attempt per load/init operation is allowed by the prompt. Failure is recorded and original tools remain usable, without counting EGRD activation.

activation.py distinguishes TOOL_NOT_AVAILABLE, MODEL_DID_NOT_CALL, TOOL_CALL_FAILED and TOOL_CALL_SUCCEEDED. Prose is never a tool invocation. Actual ADK events retain arguments, responses and monotonic timestamps. State includes ledger, hypothesis, Patch Intent, targeted/regression evidence and diff review status; edit/command calls and submit are separately retained.

Limitations: order/retry requirements are prompt instructions, not global runtime interception. Semantic Issue alignment remains UNVERIFIED until human/independent semantic review. The aggregate engineering_pass flag is limited to initialization and nonempty evidence; it does not certify full repair workflow or repair correctness. Full future workflow acceptance must independently inspect Patch Intent, production diff, current-source target/regression checks, review, submit, Native result and cleanup.

New tests cover missing tool, failed init, missing call, prose-only claim, wrong Issue hash, early exploration, response ordering and inactive/advisory behavior. The original failure logs are retained alongside passing results.
