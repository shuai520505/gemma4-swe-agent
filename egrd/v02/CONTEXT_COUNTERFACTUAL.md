# Offline reservation replay, not a repair experiment

`context_audit.py` implements the registered arithmetic and tests it directly
against the unchanged `ContextPolicy`. Context 32768 and safety 1024 stay fixed.
The scenarios change only the analytic output reservation, not any candidate.

| Reserved output | Input cap | Added input space | Archived counts admitted |
|---|---:|---:|---:|
| 16384 | 15360 | 0 | 40/43 |
| 12288 | 19456 | 4096 | 43/43 |
| 8192 | 23552 | 8192 | 43/43 |

Forty counts were actually generated; three are observed rejections. The
129 scenario rows in `SHADOW_ADMISSIONS.json` are 43 observations×3 policies, **not**
129 model actions. Both alternatives admit the first previously prevented
opportunity: A request 21,B request 13,C request 9. No later request exists to replay.

| Arm | Rejected count | Old headroom | 12288 headroom | 8192 headroom |
|---|---:|---:|---:|---:|
| A | 15607 | -247 | 3849 | 7945 |
| B | 15684 | -324 | 3772 | 7868 |
| C | 15989 | -629 | 3467 | 7563 |

All 40 observed completions are below 8192 (max 2920), with no length finish. This
establishes no observed historical completion exceeds either candidate limit;
it does not establish that re-executed or newly admitted generations would be
identical, complete, correctly formatted or useful.

## Costs, interactions and compatibility

Reducing output allowance can truncate future long reasoning, tool-call JSON,
script bodies or summaries. It does **not directly truncate sandbox tool stdout**;
tool response limits are separate harness settings. Thinking 4096 is passed to the
server, not separately added to the guard. The retained pinned vLLM usage audit
explains generated-token counting, but exact per-response reasoning shares are
unknown. Neither 8192 nor 12288 is installed here.

The pinned generation interface accepts an output cap and V03 already exercised
8192 with the compiler, guard and actual wire cap consistently changed. A future
test must change those together, never just lie to the guard. Changing a cap
does not enable compaction. If host-side compaction is enabled in another study,
its extra model generations/history/window/summary allowance become additional
factors and costs requiring separate control.

## Original V03 results independently rechecked

Archive `05bbbe36…d50580` passes SHA/CRC. Four native/config/usage records are
reconstructed in `HISTORICAL_CONTEXT_COMPARISON.json`:

- 5077:P0 true/P1 true;11355:P0 false/P1 false. Both policies 1/2.
- Guard P0=2/2,P1=0/2. Received tokens P0=465186,P1=805320(+73.12%).
- Agent seconds P0=310.423,P1=559.806(+80.34%). One P1 deadline-cancelled request
  lacks response/usage; its total consumption remains unknown.

These are exposed Action-First development tasks, not new EGR/MEER confirmation
samples or a pooled causal estimate. They directly show that fewer guard stops
and more context opportunity need not yield another native repair. This audit
therefore does not recommend 8192 as a repair-performance improvement merely
because all three PR33 rejected counts would fit.
