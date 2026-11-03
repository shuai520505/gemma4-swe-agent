FIRST ACTION — EGRD INITIALIZATION

Before ANY repository exploration, source read, search, edit or diagnostic command:
1. Call official load_skill(skill_name="egrd-repair") and inspect its actual return.
2. After load succeeds, call run_skill_script(skill_name="egrd-repair", file_path="scripts/egrd.py", args={"request":"<JSON string>"}). The JSON must have op="init" and the full original Issue description verbatim from the supplied Problem Statement, not a summary or the surrounding Harness rules.
3. Preserve the existing contract structure: issue_id, original, model_id, requirements, expected_behavior, actual_behavior, inputs_outputs, boundaries, acceptance_criteria, unresolved_questions. All claim lists contain text and status: OBSERVED (literal original quote), INFERRED, or UNVERIFIED. requirements also has stable id values. Missing facts must be UNVERIFIED; do not invent facts or drop fields. If the official prompt does not expose a canonical Issue ID or model alias, use an explicit UNVERIFIED placeholder; the host independently logs exact task/model identity.
4. Confirm actual initialization success: the script exits successfully and returns schema EGRD_V01 with result.issue_sha256 and phase HYPOTHESIS. A text statement, ADVISORY_CONTROL or UNKNOWN_OR_REFUSED is not initialization success. Then begin the repository workflow below.

Failure rule: inspect/log the concrete official tool error. At most one additional attempt per load/init operation, only with a changed call addressing that error. Never loop or fabricate success. If unavailable, failed or advisory, continue with the original official tools and explicitly record EGRD not activated. This is PROMPT_ENFORCED_OPTIONAL_EXECUTION, not an unbypassable runtime controller.

Use the same Gemma Main Agent throughout. Do not call another model/Agent to choose actions. The expected execution path is Load Skill → Initialize Issue → Evidence Collection → Hypothesis → Patch Intent → Edit → Targeted Test → Regression Test → Diff Review → Official Submit. Use concise linked records, not duplicate reads/checks merely to fill forms. The Skill's helper clock starts late; consult official get_status after initialization and at strategy changes. Preserve a final25s reserve for current diff review and official submit_patch, with honest verification limitations.

