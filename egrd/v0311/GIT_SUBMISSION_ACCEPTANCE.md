# Original native patch path: PASS for both arms

Actual new-run ADK events record the scripted sequence through the unmodified
official six tools: get_status, read_file, write_file, run_command, edit_file and
submit_patch. Host-probe read/write attempts are rejected in both arms; they are
intentional isolation negatives, not unexplained tool failures.

After source/runtime inspection, the fixture adds only an inert comment in
`django/contrib/auth/forms.py`. A normal official run_command executes the scratch
runtime assertion, deletes its scratch file, and performs `git diff --check` and
`git diff --stat`. The command succeeds in A and B. No invalid-config error occurs.

The original native `submit_patch` then returns, independently for A and B:

```json
{"status":"ok","patch_size":398,"files_changed":1}
```

This is actual tool execution, not a mocked submit response. Only model responses
are scripted. The pinned `swegemma/tools/execution.py::submit_patch` performs its
own ordinary Git diff against `_swegemma_baseline` (with its native HEAD fallback),
protected-file filtering and context submission state. Neither commands nor this
implementation are modified. The full pinned wheel identities are in CPU_BUILD.

Both exported patches are nonempty and byte-identical, SHA256
`a53facb1e7cc7a17a71af61940222c0b39063721e6aad51f5897b9d5042a570f`.
Each patch applies with `git apply --check` followed by normal `git apply` in an
independent restored original Django tree. Only the intended production file is
changed, and its Python AST remains identical. Scratch diagnostic files and native
protected workspace configuration are absent from the submitted patch.

The trusted owned probe still fails after both comments. Successful submission
and applicability do not mean a repair. Official Native Resolved and canonical
SWE-bench resolved are null. Full patches, tool responses and raw commands remain
private; public results contain identities and derived outcomes only.
