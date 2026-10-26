# Exact frozen direct-call interface

Source: original active MEER B ZIP `d962044f…f6f7c9cd`; all five member hashes
are checked before derivation. The script is **meer-evidence**, resource
**scripts/verify.py**, not a newly implemented verifier. Whole official
google-adk 1.36.1/adk-submission 0.2.13/swegemma 0.2.11 wheel identities are
validated through the retained PR35 source loader, not version strings alone.

Native tool schema (`google/adk/tools/skill_toolset.py:724–774`):

| Field | Type | Required / meaning |
|---|---|---|
| skill_name | string | Required; `meer-evidence` |
| file_path | string | Required; `scripts/verify.py` |
| args | object or list of strings | Optional at tool level; verifier needs --check |
| short_options | object | Optional; incompatible with list-form args when nonempty |
| positional_args | list of strings | Optional; incompatible with list-form args when nonempty |

Original verifier CLI (`meer/v01/verify.py`, main): `--check` is required;
`--workspace` defaults to `/workspace`; `--seconds` defaults to 10. There is no
CLI `--expected`, `--actual` or `--state-dir`. Those must not be invented.
Object-form args become `--key value` pairs in the original wrapper.

```json
{"skill_name":"meer-evidence","file_path":"scripts/verify.py","args":{"check":"/tmp/issue_check.py","seconds":"10"}}
```

This is valid **only after that actual Agent-owned Python probe exists**, is
outside the repository, and describes an Issue-relevant public-workspace check.
The Agent must supply/create such a probe through normal tools if appropriate;
the cue does not supply a repair, guarantee relevance or require a meaningless
call. Replace the example path with its real existing location. No list/load
call is a prerequisite: run_async resolves the known Skill/script directly
(skill_toolset.py:776–874). Loading instructions remains optional and useful
when the model needs them; it is not prohibited.

The preceding creation step matters: the pinned native workspace path resolver
**rejects** `/tmp/issue_check.py` as a read_file/write_file/edit_file path
(`swegemma/tools/workspace.py:22` onward). Use the normal `run_command` channel
to create/check an Agent-owned `/tmp` probe inside the permitted sandbox, after
confirming it is writable; do not route that absolute path through write_file.
`swegemma/tools/execution.py:21` onward supports sandbox shell/Python commands.
The pinned source is authoritative where the guide's broad path description
differs. A dedicated offline test verifies that rejection. Full sandbox
scratch-access validation remains part of the missing Compiler/Runner acceptance.

The original wrapper executes in a temporary Skill directory. The verifier
switches its child to the requested workspace, hashes source/check identities,
instruments executed assertions and returns a receipt. Direct routing, actual
frozen script bytes and source-bound execution were tested locally with owned
fixtures. External SDK/sandbox dependencies are explicit doubles, so this is
not a complete official Compiler acceptance or proof of Gemma adoption.

## Responses and limitations

The tool response wraps `skill_name`, `file_path`, `stdout`, `stderr`, `status`.
The stdout contains JSON `MEER_EVIDENCE_V1`: source/check SHA, assertion counts,
exception type, freshness/time/timeout and verdict. A tool status of success can
contain CONTRADICTED/UNKNOWN evidence. Missing tool arguments return
INVALID_ARGUMENTS; wrong identifiers return SKILL_NOT_FOUND/SCRIPT_NOT_FOUND.
Missing CLI --check makes the Python script fail rather than silently verify.

SUPPORTED concerns that local unchanged-source assertion execution only.
CONTRADICTED also covers ModuleNotFoundError, SyntaxError and unrelated runtime
exceptions: it is **not automatically an Issue failure**. UNKNOWN covers absent
inputs, vacuity, timeout and identity invalidation; OBSERVED suppresses an
unchanged repeat. After a source edit, old source-bound evidence is invalid and
the existing script executes against the new identity. Receipts are scratch
caches, not security attestations against malicious Agent-authored code.

The existing per-check seconds must be in `(0,15]`; cue requests 10. Official
outer executor uses the command/remaining-task bound (120-second command and
300-second Agent in this study). Python runpy does not itself inherit the
SkillToolset shell timeout. Returned receipts omit large raw output and parsing
reads only the last 64 KiB, but the temporary spool is not a hard disk-byte cap.
Windows tests cover child timeout, not Linux descendant/chroot cleanup.
