# Budget and permission audit

Candidate eval_config bytes are identical to frozen T500: max_time_minutes8.333333333333334 -> public EvalConfig approximately500s, max_tool_calls60, per-command120s. Main/child model/generation and tool schemas are byte-identical. Output16384/thinking4096/seed17; sampling and include_thoughts omitted.

One native context gates Main and child. AgentTool/get_status/submit_patch are uncharged; bound read/edit/write/run consume the shared counter. Model requests, HTTP dispatches, raw tool events and charged tool calls must be reported separately. A free submit may still occur after charged tools are denied. Child execution does not reset the Main deadline. New candidate exact500s and60-count evidence must come from this preparation, never relabel frozen results.

Child run_command can write production files despite lacking edit_file/write_file/submit_patch. The same passive hash/git-diff observer audits this; it is not a forced sandbox permission boundary. New G includes real unauthorized child write detection, cancellation propagation and missing-usage handling. A zero-write ordinary case does not establish enforced read-only access. Missing cancelled usage remains null; no GPU billing or real-Gemma token consumption is inferred from mock usage.
