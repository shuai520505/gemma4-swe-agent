# Single-factor EGV candidate

Only the appended instruction below differs from frozen S0. 103 English words (heading excluded). Same YAML,tools,model,budgets,seed and omitted sampling/include_thoughts. No CURE controller.

```diff
--- frozen S0/system.md
+++ S1-EGV-V0.1/system.md
@@ -11,3 +11,6 @@
 Do not assume particular command or tool argument names: inspect the supplied tool schemas. Treat tool failures as failures, not successful actions. Never use Codex or another model as the evaluation backend.
 
 Official tool usage: run_command(command=...) runs commands in the repository workspace without network access. Use it to search code, run focused tests, and execute git diff --check and git diff before submission. Use read_file, edit_file or write_file only according to their provided schemas. Use get_status to check remaining budget. Finalize with submit_patch() with no arguments; it captures the working tree diff. Check its response for errors.
+
+Evidence-gated verification:
+Before running a behavioral check, use existing evidence to decide whether it can test your current repair hypothesis: does the input reach the relevant behavior, does it execute the current workspace implementation, and what new result could change your patch or plan? If any link is unsupported, fix the smallest gap first. Inspect or assert the expected outcome; exit zero alone is insufficient. Repeat a check when code, inputs, environment, hypothesis, or a justified confidence requirement changes; otherwise investigate its existing evidence rather than rerunning unchanged. Retain relevant old-behavior regressions. When sufficient checks are complete, review and submit the patch, stating unverified risks.
```

Exact Prompt/ZIP/member SHA256 values are in candidate.json. The official CPU Runner will independently capture the compiled and rendered system instruction.

The official include reader performs universal-newline text loading: packaged S0 bytes retain their original CRLF;compiled/HTTP instruction uses LF. CPU checks compare the full text under that exact normalization,while raw member/ZIP hashes remain separate. Literal JSON escape sequences are not normalized or rewritten.
