---
name: egrd-repair
description: Source-bound local repair evidence and bounded decisions; not an evaluator or global gate.
---

Use run_skill_script(skill_name="egrd-repair", file_path="scripts/egrd.py",
args={"request": "JSON request string"}). State is /tmp/egrd-v01/state.json.
The same interface may return advisory UNKNOWN in a control experiment.
No result means Native Resolved or semantic proof. Official submit_patch is separate.

Initialize once with op=init, issue_id, original (exact supplied Issue), model_id,
requirements=[{id:R1,text:exact quote,status:OBSERVED}], and expected_behavior,
actual_behavior, inputs_outputs, boundaries, acceptance_criteria, unresolved_questions
(each a list of text/status claims). Implicit assumptions are INFERRED or UNVERIFIED.
After compaction consult this state rather than replacing the original Issue.

Operations (flat JSON fields):
- source: name,start,end,requirements. Reads bounded actual workspace source.
- hypothesis: location,mechanism,support (evidence IDs),contradictions,prediction,
  confidence,next_experiment,requirements. Semantic claims remain UNVERIFIED.
- intent: files,regions,behavior,requirements,support,regressions,preserve,
  discriminating_test. Then use the normal official edit_file, not this Skill, to edit.
- record_patch: observe actual differences and flag files outside the intent.
- check: path (assertion script under /tmp),requirements,purpose TARGET or REGRESSION,
  seconds (at most15). Obtain fresh executed assertions after production edits.
- review: inspect actual diff. accept: local evidence gate, never the official scorer.
- revise: bounded revision count. rollback: explicit restoration of only intent files.
- action: kind,signature,justification (optional),duration (optional observed duration).
- next: advisory next action; bypass remains possible through official tools.

Avoid bureaucracy: one concise hypothesis/intent, one discriminating target and
necessary regression checks. When the interface is unavailable, report UNKNOWN
and use the normal tools. Do not spend the submission reserve filling in records.

Entrypoint: load_skill then run_skill_script with op=init before repository work. Failure/advisory is not activation; never fabricate a contract. All Issue fields and provenance remain required.
