---
name: meer-evidence
description: Bounded source-bound assertion checks with explicit uncertainty; not an official scorer.
---

Use this skill for local repair evidence. Create a small Python reproducer under
/tmp with assertions directly tied to the normal Issue and public workspace.
Call run_skill_script with skill_name meer-evidence, file_path scripts/verify.py,
and args {check: /tmp/your_check.py, seconds: "10"}. The workspace is /workspace.
SUPPORTED concerns only this executed, unchanged-source check. It never proves
Issue coverage or Native Resolved. UNKNOWN or CONTRADICTED supplies no success
evidence. OBSERVED repeated checks supply no new evidence. After an edit, obtain
fresh evidence; inspect failures rather than repeating unchanged checks. Keep
verification small and leave time for diff review and official submit_patch.
If this interface cannot execute, report that limitation and use normal official
tools. The skill cannot intercept direct tool calls or force submission.
