# Organizer Compiler / Runner audit

Sources: [competition overview](https://www.kaggle.com/competitions/gemma-4-developer-agent/overview), supplied official HARNESS_README.md, actual wheelhouse adk-submission0.2.13/swegemma0.2.11/google-adk1.36.1, and [Google's AgentTool documentation](https://google.github.io/adk-docs/tools-custom/function-tools/#3-agent-as-a-tool). The overview URL was reached but the web text renderer exposed no body; no unseen overview text is quoted. Installed source and actual CPU behavior are the technical authority, not community implementations or unpinned latest ADK.

Each CPU preparation exports the installed modules and SHA index under results/CPU/validation/official_source*. The pinned wheelhouse hashes and effective versions are saved too. Local source inspection was followed by actual official Linux compilation/Runner execution; archived source alone was not reported as a runtime test.

| Question | Actual pinned implementation / candidate choice |
|---|---|
| AgentTool syntax | `tools: - agent_tool: {config_path: sub_agents/egv_verifier.yaml, skip_summarization: false}`; implemented by adk_submission.resolvers.tools.resolve_tool_item. |
| Paths/includes | config_path resolves relative to the current config directory with root fallback and traversal/security validation. !include uses its YAML location; child YAML includes sibling egv_verifier.md. No ../ escape or untested double-brace template escaping. |
| Child compilation | Same sandboxed compiler recursively compiles the referenced YAML; constructs Google ADK AgentTool. No competitor Python import. |
| Permissions | Each YAML resolves its own named tools against the host registry. The registry offers nine names in this wheel; S0/Main use the existing six, EGV only three. This does not force Shell read-only access. |
| Workspace | All selected functions close over the same host SwegemmaContext. The actual CPU child reads Main's changed app.py and executes its checks in that workspace. |
| State/history | AgentTool.run_async creates a new InMemorySessionService, copies non-_adk state, forwards child state_delta and returns last non-thought text. Child output_key reaches parent state. Parent Issue/Patch context must be explicit in request. |
| Summarization | skip_summarization sets ToolContext.actions.skip_summarization. false retains ordinary Main continuation. It is not an extra separate model that automatically summarizes the report. Native compaction remains separate. |
| Time | Native run_agent_sandbox wraps Runner iteration in asyncio.timeout; child work is awaited within that deadline. No independent child hard timeout is exposed by this compiler's AgentTool reference. |
| Tool accounting | Bound read/edit/write/run tools gate and increment the shared context. get_status/submit_patch are free. AgentTool itself is not decorated with budget_gated; count wrapper calls separately from charged tools. |
| Cancellation | Actual CPU native deadline and explicit parent cancellation test nested HTTP propagation; CancelledError must propagate. AgentTool source does not put its runner.close in a cancellation finally; record this cleanup caveat rather than claim universal resource closure. This candidate has no MCP resources; sandbox/process cleanup is independently checked. |
| Generation | Each LlmAgent may declare its own legal generate_content_config. This candidate fixes both to exactly the same31B/output/thinking/seed values; no model mixing/LoRA. |
| Nested audit | Default AgentTool include_plugins=true propagates parent plugins. Passive ADK hooks capture child events/models/tools plus returned report; wire dispatch and official counters are separately retained. |
| Compaction / turn configuration | The internal Runner is built from child Agent and services, not the parent's App or RunConfig. Do not assume the child inherits the parent's compaction/cache configuration or per-invocation max_llm_calls. The same client admission guard still bounds each outgoing request, and the native enclosing300s deadline is shared. |
| ZIP | Root agent.yaml, eval_config.yaml, main Prompt, child YAML, child Prompt. Official validation/compilation is exercised on extracted ZIP bytes. |

Tests also preserve intentionally failed paths: unavailable child edit_file, actual Shell production writes, unknown/empty reports, stale false PASS reports after failing tests, native command timeout, cancelled child HTTP, exhausted shared tool budget, and actual submit_patch errors. These are API failure tests, not claims that Gemma attempted those actions.

Candidate Prompt/state text avoids literal brace placeholders. JSON braces occur only as synthetic task input in the empty-State Runner test; real rendered requests preserve that task content. No custom callbacks, controller code or evaluation answers enter the ZIP.
