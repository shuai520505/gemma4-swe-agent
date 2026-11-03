# Bounded patch lifecycle

HYPOTHESIS → PATCH_INTENT → PATCH_CREATED → PATCH_TESTED → PATCH_REVISED or PATCH_ACCEPTED.

Intent requires existing fresh evidence and Issue IDs. record_patch observes actual changes and refuses an empty patch. New recorded source variants consume the configurable revision allowance (default2); explicitly calling revise reserves a revision ticket instead of permitting a bypass. A direct edit can still bypass this bookkeeping; no global revision cap is claimed.

check records fresh targeted/regression evidence. review_diff binds the inspected source hash and actual Diff. Local accept requires a recorded nonempty patch, no files outside intent, current diff review, current linked passing target/regression checks, and no fresh failed counterexample. After another source edit both acceptance and diff review become invalid. The last patch is never accepted automatically.

rollback restores only the explicitly snapshotted intent files; it is an explicit operation, not a claim to rank multiple patches or identify the semantically best repair. No reference answer or evaluator verdict selects the snapshot. There is no automatic search over many candidates.

LOCAL_CHECKS_SUPPORTED means those executed local assertions support the current byte identity. It does not mean Issue completeness, independent semantic approval, hidden Native Resolved or a successful official submission. The ordinary official submit_patch remains separate and can be called without using EGRD.


Current CPU correction: diff is computed against the initial session Git revision, so staged/committed tracked changes remain visible. Untracked new files are explicitly listed as unreviewed and block local acceptance until they are included in a Git diff (for example by the normal official command tool's git add -N) and reviewed again. The helper does not silently alter the Git index. Pilot-frozen predates this correction; no real-model evidence is claimed for it.


Configuration boundary: revision/reserve values are configurable through the core Python state API, as exercised by unit tests. The deployed V0.1 CLI freezes defaults of2 revisions and25s reserve; dynamic YAML/CLI override binding is not implemented and would require a separately versioned package/retest.
