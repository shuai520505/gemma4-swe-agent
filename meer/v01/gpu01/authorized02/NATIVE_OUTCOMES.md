# Native outcomes

| Run | Task | Arm | Agent executed | Native Resolved |
|---|---|---|---|---|
| 1 | fastapi_14297 | A EGR | no | null / NOT_RUN |
| 2 | fastapi_14297 | B MEER | no | null / NOT_RUN |
| 3 | fastapi_14297 | C advisory | no | null / NOT_RUN |
| 4 | fastapi_14459 | C advisory | yes | false |
| 5 | fastapi_14459 | B MEER | yes | false |
| 6 | fastapi_14459 | A EGR | yes | false |

Batch1's outer Notebook entry failure is infrastructure, not three algorithm
failures. Batch2 is COMPLETE with three negative native evaluations: each has
8unique tests,2call assertion failures and2exact paired snapshot teardown
records. The frozen PR26/PR30 interpretation was independently reapplied to the
original JUnit bytes: zero independent environment errors. Native false and
test exit1 remain unchanged; no original tests, XML or evaluator were edited.

A returned887bytes of diagnostic-file-only diff. B/C returned empty patches.
All three made zero observed production-source changes and zero explicit
submits. An unsubmitted diagnostic diff is not a behavioral repair.

The valid success denominator is0/3actual sessions, or0/1observed task for each
arm. It is not0/6sessions or0/2tasks per arm. The intended two-task matched
experiment is incomplete. TaskResult/JUnit/patch hashes and cleanup are in
`SESSION_RESULTS.json` and `BATCH_02_RUNTIME_AUDIT.json`; originals remain private.
