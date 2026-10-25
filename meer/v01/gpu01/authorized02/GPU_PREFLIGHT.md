# Owner-authorized MEER execution

The owner explicitly authorized the frozen PR31 six-session experiment in the
conversation. `GPU_AUTHORIZATION_RECORD.json` preserves that external grant;
historical `GPU_authorized=false` preparation records remain unchanged.

## Static gates and dispatch

- A: all three original ZIPs and member hashes were independently rechecked;
  the shared production ZIP has 205 pinned files plus its registration manifest and SHA256
  `38170bc0d6684ea09097d106cb0a4fbcf5fbc67a0b7c061f139ae99bccc558b5`.
- B: original PR30 admission ZIP, TaskResult, JUnit, task/snapshot/overlay
  identities and cleanup were re-read. The exact paired snapshot teardown
  interpretation for `fastapi_14459` remains frozen. No replacement task.
- C: model input availability, pinned files, compiled candidate configuration
  and original CPU evidence were checked before dispatch. Actual device,
  weight rehash, dependency and model-service gates run inside the Notebook;
  their results must be assessed from its archive, not inferred from CPU tests.
- D: finite CLI reads checked current quota, zero GPU reservation, latest ten
  date-run job statuses and each exact unused slug. An earlier overly broad
  historical sweep was stopped and preserved. Inaccessible historical entries
  are not converted into terminal statuses. PR27 Batch2 remains UNKNOWN.
- E: source, shared payload, outer Notebook, owner grant, task order and limits
  were bound before each once-only save. HTTP receipts and independent read-only
  source/ID/version recovery are retained. A CLI `None` result left the inherited
  journal UNKNOWN_STOP; the later HTTP200 and resource identity evidence are
  separate records, not rewritten journal entries.
- F: the grant permits two distinct task batches, three sessions each. Both
  GPU dispatches are now consumed. A third GPU save or session retry is forbidden.

## Observed entry failure and bounded repair

Batch1 `140782899/v1` ended ERROR before the coordinator body started:
`asyncio.run() cannot be called from a running event loop`. No model or Agent
started. Actual GPU allocation was not observed because that gate was not reached.

CPU `140784340/v1` completed the existing official Worker/Skill/native synthetic
path using top-level `await` inside the actual Notebook event loop. All 205
shared production members matched; 35 HTTP calls were SCRIPTED_ONLY. This is
engineering evidence only. The Batch2 outer Notebook changed its invocation to
top-level `await`; shared production bytes and frozen candidates did not change.

Batch2 `140785918/v1` retains only the original `fastapi_14459` C/B/A sessions.
It is not a retry of the omitted `fastapi_14297` A/B/C sessions. Its actual
runtime and final outcomes are recorded separately after collection.

## Review order

Issue, visible tool checks and observed source-version changes are reviewed and
hash-locked before opening the Agent's native results. Native outcomes remain
independent of local check verdicts. No hidden test or reference fix is used to
construct or amend any candidate.

## Final runtime gate assessment

Artifact/task/owner-authorization gates passed their independently checked
bindings. Batch1's execution gate failed at the outer entry; dynamic device and
model gates were not reached and are not retrospectively called PASS. Batch2
then passed actual allocation,8weight/tokenizer/template hashes, dependency
fingerprint, common Guard/generation binding, native evaluator, synthetic chroot
canary and cleanup checks. All40real model responses are HTTP200. Its Skill
tools are exposed in real request schemas, but the optional script path is not
exercised by Gemma; that absence is an adoption outcome, not a fabricated script
compatibility result. The final six-session experiment remains PARTIAL.
