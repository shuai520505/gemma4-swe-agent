# Tool-evidence audit definitions

Use native Agent-start monotonic time as zero. Model prose is not an event.
First production modification is the completion time of a successful tool
operation whose returned content and eventual diff establish a production-file
change. It is separate from first edit attempt. Label correctness retrospectively
using contract, Patch content and actual Phase2; an early wrong change remains
negative evidence even if later repaired. If content evidence is insufficient,
the first effective-edit value stays unknown.

Count all actual function-call events before that successful modification.
Pair each call with its actual response by ID. Distinguish schema/tool errors,
nonzero commands, expected reproducer failures and unrelated failed commands.
A failing targeted regression before an edit can be useful evidence and is not
automatically low-value exploration.

Exact repeated reads require the same successful filepath/arguments. Report
overlapping line ranges separately from exact repetitions; overlap can be useful
if a changed file or a concrete new question justifies it. Semantic low-value
search/read classification requires manual content/context review and identified
event numbers, not just duplicate-string counting.

Workspace module execution requires actual passive provenance, not exit0.
Changed-behavior verification additionally requires a relevant executed assertion;
module import alone does not prove changed-function coverage. Retain gaps rather
than upgrading path evidence to correctness. Explicit submit requires a successful
submit_patch response; fallback Patch extraction is reported separately.

Native resolved/test_exit_code, Phase2 stdout/stderr and Patch/apply events are
never overwritten. Count only observed HTTP response usage, keyed by request_id.
Partial/unreceived usage is unknown, not zero; full Token deltas require complete
usage in both arms. Separate Agent elapsed, worker elapsed, startup and Notebook
allocation time. One control-first pair has order/cache confounding and no
population repair-rate estimate.
