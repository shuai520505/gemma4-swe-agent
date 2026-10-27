# EGRD V0.3.2 — real Gemma evidence-to-patch A/B

Final status: **EGRD_V032_NEITHER_REPAIRS**. Private Kaggle141100028/v1 COMPLETE;
one GPU dispatch, exactly A→B real Agent sessions, four L4 GPUs and frozen S0.
Neither produced a submitted verified repair. A made a late unverified production
edit; B edited tests/scratch only. Neither fallback was evaluated as a submitted
patch. See FINAL_DECISION.md and AB_RESULT_ANALYSIS.md for the key limitations.

Reproduction: validate archive using inspect_results.py (private verified-output
must not already exist), then `python -m egrd.v032.finalize_results`. Run
`python -m unittest egrd.v032.test_preflight egrd.v032.test_results -v` for offline
integrity and missing-data/endpoint checks. No analysis utility performs model
inference, Notebook dispatch or competition submission.

The exact original S0 ZIP, task, receipt, generation settings and tools remain
unchanged. The only A/B input intervention was the frozen B receipt. Real serving
token overhead678; no seed17, later research Guard, compaction or new Skill.
No official Native/SWE-bench evaluation or new Public Score. Historical S0
serving equivalence remains unverified. S0 remains the formal0.13 baseline.

The earlier no-dispatch stop is preserved in PRECLARIFICATION_STOP.json and Git;
the owner clarified that unrelated concurrent jobs are permitted. A single
subsequent dispatch was accepted; no duplicate, rerun, cancellation of another
job or additional Session occurred. Candidate and historical artifacts were not
altered. Raw task, reasoning, tool/HTTP traces, evaluator files and patches remain
in the controlled private archive; Git contains safe derived records only.
