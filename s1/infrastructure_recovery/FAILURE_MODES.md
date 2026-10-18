# S1 A trajectory: failure modes and priorities

Evidence is the immutable `s1-e1-outputcap-smoke-02` A trace. B never ran.
Observed behavior cannot establish a causal improvement from E1, E3 or E4.

| Observation | Supported interpretation | Not established |
|---|---|---|
| First production edit 258.497s of 300s | 86.2% of budget spent before repair; only 41.503s remained | E3 would necessarily edit earlier or correctly |
| 23 tool attempts / 22 official calls, no submit | Time, rather than the 60-tool count, bound this run | Increasing tools would help |
| Missing filepath, absent file, uninitialized headers | Multiple reproducer attempts produced tool/fixture errors | More investigation was inherently useful |
| Hand-written old slicing logic ran twice | Its output was independent of the workspace edit | Its exit 0 verified the changed Requests implementation |
| A traceback used system Requests; final check did not prove workspace import | Validation provenance was inadequate | A final passing script established repair success |
| max observed input 10899, output 3230, no observed length finish | Neither observed context nor output cap bound completed responses | B=8192 is safe on all tasks, or would improve this one |
| Native Phase2 194 fixture setup errors | Verdict needs environment attribution | resolved=false is evidence of an algorithm-specific failure |

## E3: earlier evidence-based editing

Frozen E3 limits search scope, requires each additional read to resolve an
unanswered question, and says to edit/verify once a small repair plan is
supported. It might reduce overlapping reads, dead searches and large bespoke
reproducer generation. It does not guarantee that a smaller investigation
finds the correct contract, and premature editing could increase regressions.

Measure successful production-diff time from tool results, not a write attempt;
time and calls before that edit; repeated/overlapping reads; failed tool args;
production versus diagnostic files; verification after edit; and successful
explicit submit before cutoff. Preserve incorrect early edits as failures.
Use fixed budgets, not a new timing nudge, forced edit deadline or extra tools.

## E4: meaningful verification

Frozen E4 asks for repository-grounded import/export names, callers/entry
points and contract-directed behavior plus boundary/old-behavior checks. It
does **not** explicitly require printing __file__, and cannot be described as
already fixing wrong-package imports. This recovery supplies editable setup
and passive provenance equally to control and E4. Their infrastructure benefit
must not be counted as the Prompt factor's benefit.

Measure whether a post-edit check actually loads/executes workspace module
code, asserts the changed contract, covers a relevant boundary/old behavior,
and completes before submission. Track invalid scripts and repeated tests.
Path evidence alone is not coverage; exit 0 alone is not path evidence.

## E1: when context headroom could matter

With 32768 context and 1024 safety, cap16384 permits 15360 input tokens;
cap8192 permits 23552. This A peaked at 10899 and retained 4461 slack. The two
compactions already bounded history, and all observed completions were below
8192. There is no observed context-pressure benefit in this run.

E1 is most informative on predeclared tasks with large Issues/tool schemas or
long indispensable histories that approach/exceed the 15360 input allowance.
Use baseline admission/slack distributions and rejection counts to choose a
separately registered context-pressure study. Do not increase file dumps or
disable compaction just to manufacture a win. Lower cap can truncate useful
thinking/actions, so finish reasons, failed tool JSON and Patch quality matter.

## Decision: E3 first, E4 independently next, E1 deferred

This ordering is an engineering hypothesis: late editing is observed, while
context pressure is not. E4 remains important after common source/environment
admission is reliable. No Prompt fusion or E3+E4 package is introduced.
If a selected task fails its CPU environment gate, its GPU experiment remains
blocked; do not silently substitute an easier task after seeing outcomes.

The next draft freezes one fresh Rich task for E3 and one fresh FastAPI task
for E4 before their CPU readiness results. Each is a two-run mechanism pilot,
not an estimate of population repair-rate improvement. Fresh tasks reduce
direct development exposure; public pretraining contamination remains possible.

Use the same 31B, seed17, 300s/60 tools, output16384/thinking4096, omitted
include_thoughts/sampling defaults, executor and snapshots in each pair. No
unmetered model or task-solving probes are added. Report setup costs separately;
audit I/O remains within actual command/Agent elapsed time for both arms.
Compare task-specific mechanisms first, actual native Phase2 second, and never
transfer another model's or another competition's scores to these pilots.
