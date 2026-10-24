# Competition compliance, pinned implementation scope

Primary sources: [organizer competitor guide and official wheels](https://www.kaggle.com/competitions/gemma-4-developer-agent/data), [official starter](https://www.kaggle.com/code/ryanholbrook/getting-started-gemma-4-developer-agent), [evaluation](https://www.kaggle.com/competitions/gemma-4-developer-agent/overview/evaluation), [rules](https://www.kaggle.com/competitions/gemma-4-developer-agent/rules). Current overview/evaluation/rules web reads returned no body lines. Thus no claim is made about an unseen private scorer or unobserved current rules. CONFIRMED below refers to the pinned official competitor guide plus actual organizer distribution and, when completed, real CPU execution. No private infrastructure change is permitted.

HARNESS_README.md lines65-144 describe declarative-only configuration, four built-in Agent classes, AgentTool, skills, allowed .py skill scripts and fixed registries. Hashes and installed-module identity are in OFFICIAL_SOURCE_PINS.json and CPU evidence.

| Capability | Classification | Evidence / exact boundary |
|---|---|---|
| Built-in LlmAgent/SequentialAgent/ParallelAgent/LoopAgent YAML | CONFIRMED_ALLOWED | Official guide2.3, schema.py; use only registered classes |
| Arbitrary Python custom BaseAgent / agent.py host entry | CONFIRMED_PROHIBITED | Declarative-only contract2.1; compiler never dynamically imports competitor entrypoints |
| ADK sub-agents / AgentTool, same allowed model | CONFIRMED_ALLOWED | Guide2.3,3.2; schema AgentToolEntry. Not selected |
| Skills and sandboxed Python scripts | CONFIRMED_ALLOWED | Guide2.2,allowed extensions; native Runner provides AdkSandboxCodeExecutor to compiler; actual skill route is the CPU acceptance target |
| Arbitrary host tool wrappers or new registry Python functions in ZIP | CONFIRMED_PROHIBITED | Closed ToolRegistry; unsupported host code entry not an allowed tool definition |
| Custom before_tool/before_model Python callback controller | UNVERIFIED / NOT_AVAILABLE in pinned official Runner | schema accepts callback names, but resolver callbacks.py84-85 returns empty if callback_registry is None; native run_agent_sandbox supplies none. A YAML callback name is not enforcement. No custom registry is injected |
| Preapproved organizer callbacks if supplied by organizer | UNVERIFIED | No enabled callback registry/names established |
| Task-local scratch evidence state | CONFIRMED_ALLOWED | Skill scripts execute in task sandbox and can read/write /tmp; state is not trusted and never shared across sessions |
| Trusted persistent host state / cross-task history | UNVERIFIED, excluded | No supported competitor API established; would introduce contamination |
| Built-in declarative workflow orchestration | CONFIRMED_ALLOWED | Guide2.3/schema workflow classes; same single-model rule and budgets apply |
| Arbitrary Python host orchestration / modifying Runner or Verifier | CONFIRMED_PROHIBITED | Not a declarative submission extension; rejected for this design |

Six official workspace tools remain byte/schema intact. Skills add official list_skills/load_skill/load_skill_resource/run_skill_script declarations; six is a frozen baseline design, not the competition's universal tool count. This unavoidable A/B interface difference is controlled by C, which has the same SkillToolset and metadata but no verifier execution. The script uses no network, install, hidden test, reference patch, evaluator access or unofficial model.

The helper cannot intercept direct run_command/submit_patch, cannot revoke tools, and cannot force submission. Script time is bounded by both the native executor and a tighter local15s limit. Organizer budget accounting is preserved, including any native distinction between charged workspace calls and skill invocations; extra Skill calls/latency are reported separately, not hidden as free computation.
