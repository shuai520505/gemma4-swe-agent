# Early verification design

Before a Patch, Main may ask one bounded falsifiable question after locating relevant code. Its request supplies Issue requirement, paths, hypothesis, expected behavior, actual evidence, explicit no-Patch status and remaining budget. EGV executes actual assertions/provenance/regression checks, then returns the unchanged feedback protocol. It must not claim an existing Patch or repair production code.

The child instruction already verifies the Main hypothesis against the Issue and current workspace; it does not require a Patch to exist. CPU A explicitly invokes it before any edit with app.py hash still equal to baseline; CPU B receives the real failing assertion and repairs/retests/submits. This tests compatibility, not a model decision to delegate.

After a substantive Patch, CPU C retains the old wrong-Patch -> child failure -> actual Main correction -> child target/old-behavior pass -> submit chain. An acknowledgement, child FAIL or edit alone does not count. Valid child counterevidence must be delivered, handled with production change or evidenced exclusion, and followed by discriminating successful retest. Zero actionable counterexamples means loop-rate denominator0/null.
