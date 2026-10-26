# EGRD V0.2 final decision

**EGRD_V02_AUDIT_COMPLETE_MORE_EVIDENCE_REQUIRED**

The offline audit is complete. No new production Agent, controller or candidate
was built. S0, frozen candidates and original results remain unchanged. The
registered context boundary is independently reproduced; a compliant, useful
global evidence-compaction implementation is not yet established.

## Required findings

1. **Why all three stops?** A/B/C next inputs were 15607/15684/15989, above
   `32768 - 16384 - 1024 = 15360`. The wrapper rejected generation before vLLM,
   with nominal Agent time and tool allowances remaining. This is neither a
   backend generation error nor a 300-second timeout.
2. **What consumed context?** The original Issue, system/Skill instructions,
   tool schemas and accumulating assistant/tool history. All 40 sent requests
   preserve the Issue once and extend the prior message prefix. There is no
   observed compaction or duplicate-message insertion.
3. **Identifiable growth?** Initial-to-rejection growth is 13408/12685/12990.
   Entire interactions associated with read_file account for 4098/8839/11726,
   respectively. These include assistant text, arguments, results and framing;
   they are not isolated source-output token counts. B/C have an additional
   800 initial tokens from their combined instruction/interface differences.
4. **What remains unmeasurable?** Exact rendered component token counts, separate
   thinking usage, the final unsent generation bodies, future generations, and
   official leaderboard per-task trajectories. Exact local tokenizer/template
   bodies are unavailable. Character counts are explicitly not token estimates.
5. **What does 8192 shadow establish?** All 43 observed token counts would meet
   that admission boundary, including three originally rejected opportunities.
   Only 40 generations actually occurred. It establishes no future trajectory,
   output-safety guarantee or Native Resolved improvement. The old V03 pilot
   removed guard stops without adding native successes and increased costs.
6. **Why no production edits?** A's five scratch executions never establish a
   valid failing contract check; later checks print results without assertions.
   B/C continue inspecting plausible code and questioning causal hypotheses.
   All stop before a production change. Their exact internal reason for not
   editing is unknown; source inspection does not prove root-cause understanding.
7. **Demonstrably low-value actions?** A changes route order while its scratch
   dependency graph is still incorrectly declared, and attempts an exact-string
   edit that fails. Printed/non-failing examples do not distinguish the target
   defect. Repeated commands follow changed scratch code, so they are not five
   unchanged-check repetitions. Most B/C source reads provide new code.
8. **Was an earlier edit justified?** No observed opportunity establishes an
   already supported correct behavioral edit. Five recorded opportunities favor
   a better discriminating probe or reproducibility check, not a hindsight patch.
   Proposed alternatives remain unexecuted and their outcomes are unknown.
9. **Which intervention has stronger support?** Context termination is the
   stronger established mechanical constraint. Evidence gathering/verification
   defects also exist, especially in A. A general evidence-to-patch decision gap
   with a defensible edit already available remains plausible, not established.
10. **What is executable through the pinned interface?** Native tools, supported
    workflow configurations and sandboxed Skills. A Skill can hash source,
    execute checks and report stale evidence after invocation. It cannot force
    invocation, govern all tool calls or rewrite host conversation history.
    App compaction exists in the library but the actual Worker disables it;
    no competitor-configurable global hook is verified. Callback names without
    an executable registry are inert. `include_contents: none` retains the
    current single-task tool chain.
11. **Which minimal mechanism first?** None is approved for implementation yet.
    The single next diagnostic priority is evidence-preserving context-projection
    feasibility: exact rendering replay, a verified deployment hook and an
    explicit preservation policy. Almost no read overlap exists (one line among
    1833 returned lines), weakening a simple repeated-read cache proposal.
12. **What would it change?** If those gates pass, only selected accumulated
    history would be projected before request construction. The exact Issue,
    current source/patch identities, adverse observations, unresolved questions
    and valid recent tool-call/result pairs must remain. It would not change
    output caps, Prompt, native evaluation or tool semantics.
13. **Expected overhead?** Unknown; no production mechanism exists to benchmark.
    A deterministic projector would add CPU processing and zero additional model
    calls by design, subject to verification. At most one second of total
    projection CPU per Session is a proposed acceptance target, not a measurement.
    Current Skill-interface initial overhead of 800 tokens is measured.
14. **Falsification?** Loss of necessary adverse evidence, new repair regressions,
    or reduced guard stops with unchanged native repair and higher cost would
    undermine usefulness. If no supported hook exists, this deployment design
    is blocked regardless of research-host compatibility.
15. **Smallest credible matched experiment?** After interface/preservation gates
    and separate authorization: two newly admitted tasks, four independent
    Sessions, alternating inert passthrough versus active projection through
    the same interface, with all other inputs/configuration fixed. This is a
    conditional protocol, not a ready candidate or permission to dispatch.

## Scope and validation

Original PR33 evidence independently checked: three real Sessions, 40 model
requests/responses, 40 tool actions, three native false outcomes and three
unexecuted task/arm outcomes retained as null. Received usage is 314334 tokens.
Four original V03 result/config/usage records provide a separate historical
comparison. PR32's 26-session audit is hash-verified prior work, not a newly
repeated raw-trajectory review.

Fourteen deterministic offline tests pass. Source checks verify three official
wheels, 206 shared payload members, 205 registered pins, eight recorded model
file identities, candidate ZIPs and original native result/JUnit hashes.
These are offline evidence and interface-helper tests, not a new Agent run.

No Notebook save/dispatch, model generation, GPU use, formal submission,
package installation or historical PR merge occurred. Public outputs contain
derived metrics/provenance rather than raw private trajectories, evaluator
content or patches. Do not replace S0 or predict a Public Score from this audit.
