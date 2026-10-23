# U-RE V0.3 Context Budget Pilot

Experiment `U-RE-V03-CONTEXT-BUDGET-01`, derived from open/unmerged PR27
`e3fe17d56c05b6a52442b329450dcd88d0c80bcc`. This is a mechanism pilot on two
previously observed FastAPI tasks, not an independent confirmation sample.

Both policies use the byte-identical Frozen Action-First V0.1 instruction and
the same Gemma4 31B QAT v2, TP4, four L4, 32768 context, safety1024,
thinking4096, seed17, 300s/60charged tools/120s command. Only the compiled
maximum output changes: P0=16384/input15360; P1=8192/input23552.
`policy.py` supplies both the official Compiler's ephemeral research YAML
override and the actual model client's unchanged reservation guard. Original
candidate directories, ZIPs, official Runner/tools/Verifier and old results
remain untouched. No new prompt or context compression is added.

Frozen order is 5077/P0, 5077/P1, 11355/P1, 11355/P0. `CONTEXT_POLICY_FREEZE.json`
and production bytes were committed before the actual CPU and GPU requests.
Two unused CPU draft builds were superseded before dispatch; only
cpu-e2e03 (`140394362/v1`) was saved. Its actual packaged entry completed both
scripted synthetic policy Sessions and the two native real-task baselines.
The raw CPU archive is required again by the GPU launch gate.

One GPU SaveKernel was sent for `140395342/v1`; independent read-only source
and resource confirmation follows the original journal's UNKNOWN_STOP, without
rewriting that historical event. No second GPU dispatch is authorized. PR27
Batch2 remains SAVE_STATUS_UNKNOWN; its HTTP499 is not a rejection. Before this
new dispatch, current official resource reservation was0s, remaining report
quota76209.100s, complete owned listing found no slug conflict or visible active
GPU collision. A distinct status operation for old Batch2 returned403; no prior
acceptance/execution result is inferred from its current invisibility.

`OFFLINE_OUTPUT_DISTRIBUTION.json` derives safe per-request statistics from both
actual historical private archives. Exact separate reasoning token usage and
per-tool token attribution are UNKNOWN. Character counts are not token counts.
`CONTEXT_SHADOW_ANALYSIS.json` makes no repair claim or trajectory prediction.
P2=4096 is offline only; thinking4096/output4096 would fail the existing Config's
requirement to leave room for actions and is not a proposed executable policy.

Raw model/tool trajectories, evaluator text, native JUnit/TaskResult and complete
patches remain under controlled private evidence outside Git. Public files
contain source, immutable identities, derived statistics and redacted status.
Final state: `V03_CONTEXT_PILOT_COMPLETE`, four real Sessions. Both policies
resolved5077 and failed11355 (1/2each). P1 eliminated both observed guard stops
and admitted larger inputs, but increased received tokens73.12% and Agent
time80.34%; no new repair. One deadline-cancelled request has UNKNOWN usage.
Final results and H1–H6 assessment are in `FINAL_DECISION.md`.
This study creates no Competition Submission and does not change a formal entry.
