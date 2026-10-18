# s1-e3-localize-smoke-03

This study is authorized for **one** real GPU pair, control then frozen E3, on
`rich_3278`. No other factor, task, training or leaderboard submission is allowed.
Parent commit: 4d81fd7368d8ae1d4f9a4ccb5fbbc90099f3beb4. This document, exact
protocol.json, Notebook/payload hashes and passing CPU evidence must be pushed
before GPU dispatch. Registration status is prospective; completion is recorded
in new result files, not by rewriting protocol or historical evidence.

## Frozen treatment and inputs

Control uses the original S0 Prompt; frozen E3 adds hierarchical localization.
Both use the existing S1 operational configuration (not a reproduction of S0's
score). Control ZIP SHA256:
`8835fd8ab4bdd43f5fcf74423c8ed2c3b9e0e0711686c8eac335b22c1da9da12`.
E3 ZIP SHA256:
`ae5e6157d2e96b20ffb4c9dd54902313cffeb9d1f9bdd231c38ef4eafbca7461`.
Exact member and source hashes are in protocol.json/registration.json. Agent
configuration and eval_config are identical between arms; only Prompt differs.

Task base: 4c5d305bb902ce97011666ada19e48d0b27b49e1.
Issue SHA256: 665a4e2e3fc95e55e496f73945d905a5a0df5e30335fcf387b61655c41155b1d.
Snapshot SHA256: bda96e09e9e02fa372b2cf6c5f3f2760f97d292fb531cc631564632940d6a453.
Selection was fixed in the prior recovery draft. Do not substitute after outcomes.
No prior Patch, model trajectory or evaluator test content is supplied to Agent.

Gemma4 31B QAT version2; 4 L4 / TP4; context32768; safety1024; output16384;
thinking4096 inside output; seed17; Agent300s; 60 tools; command120s. Single ADK
Agent, six official tools. include_thoughts, temperature/top-p/top-k remain
omitted as in both frozen candidates. Model/wheel file hashes are pinned, not
merely version labels. No LoRA or private task-solving controller.

## Mandatory gates and isolation

1. Verify all 97 recovery-test source bytes against the accepted raw payload,
   then replay those tests in the pinned official Linux CPU image. Actual
   Compiler/empty-state Runner/HTTP path includes control and E3.
2. Test the new read-only scheduler-metric parser. A missing metric is unknown,
   not zero. Candidate YAML/ZIP/Prompt bytes must remain frozen.
3. Recheck original Rich baseline imports/tests, and run **actual native
   verify_task** on the clean unrepaired base with the original evaluator patch.
   Reference repair is never loaded. Expected assertion failures are valid
   environment evidence; missing tests/fixtures/imports/setup errors are not.
4. Repeat native evaluator-only environment readiness on the GPU host before
   loading the model. Keep all preflight artifacts outside Agent workspaces.
5. Verify actual GPU identity/model files/config; health/models, one real
   startup completion, tokenizer/usage equality and actual oversize rejection.
6. Require three server-reported /metrics snapshots >=1 second apart with zero
   running and waiting requests before tasks and after each completed worker.

Fresh worker, official base snapshot, Agent state and native Phase2 sandbox for
each arm. Neither arm sees the other's Patch, reasoning or discoveries. Cached
build dependencies and passive import auditing are identical common infrastructure,
not an E3 benefit. No task-solving probes are performed on the Agent's behalf.
Observation I/O consumes real command/Agent time; no compensation budget.

## Budgets, cancellation and global stop

Global clock starts before installation/hash/model loading:10800s, with900s
finalization held back. Native Agent300s and verifier300s remain unchanged.
Each outer slot1350s plus60s scheduler-reclamation observation must fit before
the next worker starts. Startup readiness has1200s bound. No blind continuation
when remaining time is inadequate for a complete task and finalization.

Every actual model dispatch is assigned a request_id with exact raw body,
status and one terminal. A CancelledError must be observed and re-raised, joined
to the native registered deadline and Agent-end event within2s, plus independent
worker/sandbox cleanup. Missing response alone is never a cancellation proof.
Unreceived usage remains null/partial; do not report a full cost delta from it.

Client cancellation does not prove server cancellation. Running/waiting gauges
must become observably idle before continuation; missing gauges or nonidle for
60s stop the study. These post-worker samples establish reclamation by that
observation time, not immediate abort latency or the unreceived token count.
Preserve server logs and final server-process-tree cleanup evidence separately.

Stop globally on model/source/config/hash drift, transport failures, unexplained
request terminals, unverified server reclamation, environment/collection/setup
errors, missing native Trace/Patch/Phase2, possible evaluator-answer access,
workspace contamination, cleanup failure or insufficient time. Empty Patch
fails the complete infrastructure gate. A valid applicable Patch with an
ordinary assertion failure is retained and may continue if all gates pass.
Unstarted arms are not_run; unattribuable environment results are unknown.
Never retry, hotfix or splice old trajectories into this experiment ID.

## Mechanism audit and decision

Audit actual tool arguments, results and resulting source changes, not model
self-report. Record first correct-location read, first successful production
diff, pre-edit tool count, repeated exact reads and overlapping line ranges,
failed tools/commands, later reversals, post-edit workspace module execution,
contract assertions, submit, final Patch/applicability, native Phase2/resolved,
all HTTP/ADK events, observed Token completeness and elapsed time.

Earlier edit alone is not success. An early wrong edit, unsupported assumption,
lost verification or broken Patch is negative evidence. Separate first successful
file modification from retrospective correctness; if correctness cannot be
established, do not label the edit effective. Source import provenance proves
module execution, not changed-function coverage without relevant assertions.

No-Go on infrastructure loss or harmful premature edits. A Go recommendation
requires a complete auditable pair plus evidence that E3 changes investigation
usefully without sacrificing Patch correctness or verified submission. Even a
positive single pair supports only a new preregistered multi-task confirmation,
with balanced order and fresh tasks. Fixed control-first order creates cache/order
confounding, so small timing changes are not causally conclusive. No overall
repair-rate gain or new Kaggle score is established by this smoke.
