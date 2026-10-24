"""Matched interface with advisory guidance, deliberately no evidence mechanism."""
import json
print(json.dumps(dict(schema="MEER_PROMPT_ONLY_CONTROL",verdict="UNKNOWN",
    observed=False,subprocess_invocations=0,
    guidance="Use official tools to run your Issue-relevant assertion reproducer. Check that it executed after the latest source edit; do not repeat unchanged diagnostics. Passing an assertion does not prove the whole repair. Review the diff and submit when justified.")))
