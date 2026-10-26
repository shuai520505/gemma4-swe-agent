# Prompt single-factor audit

Both arms derive from the frozen active MEER B ZIP. Only prompts/system.md differs; all four other members match each other and the original byte for byte. Removing the inserted cue recovers the original Prompt exactly. No instruction outside that block changes.

The cue begins after the original opening paragraph and before Evidence-guided repair in both arms. Both mention an existing optional Issue-relevant probe; D adds the concrete route/arguments and lack of discovery prerequisite. This is adoption guidance, not enforced execution or an active/inert verifier contrast.

N cue: 43 whitespace words / 313 characters. D cue: 41 words / 428 characters. These are not model tokens. Exact rendered initial token counts and their difference remain UNKNOWN; no surrogate tokenizer or semantic filler is used. Added identifier/syntax salience and unequal token length remain part of the intervention.

```diff
--- N/prompts/system.md
+++ D/prompts/system.md
@@ -5 +5 @@
-Its executable verifier and resources are available through the declared Skill interface; use the real probe path if you choose it.
+With an actual probe at /tmp/issue_check.py, call run_skill_script with {"skill_name":"meer-evidence","file_path":"scripts/verify.py","args":{"check":"/tmp/issue_check.py","seconds":"10"}}; substitute the real path. No list/load call is required.
```
