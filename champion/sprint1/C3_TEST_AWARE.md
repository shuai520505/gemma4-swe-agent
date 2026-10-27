# Identify a runnable test before executing it

Use repository evidence to choose the test entry point. Inspect the relevant test
directory and the applicable project instructions, scripts and configuration:
pyproject.toml, pytest.ini, setup.cfg, tox.ini or manage.py when they actually
exist. Do not read every configuration file by default. Check the project's
documented invocation and dependency declarations rather than assuming a root
manage.py, a pytest executable, or a particular test-label format exists.

Interpret command results precisely. Separate an issue-related assertion failure
from a missing import/dependency, nonexistent entry point, missing settings,
uninstalled test framework, collection failure or command timeout. A check that
does not execute the target behavior supplies no evidence that the repair is
right or wrong. A successful exit without relevant executed assertions is weak
evidence; retain that limitation.

When a test route cannot run, do not cycle through guesses at equivalent command
spellings. Use the error and actual project configuration to select a different
supported route. If the framework is unavailable, prefer a small targeted check
using the runtime already present, with required initialization before imports
that depend on it. State what it checks and what result would contradict the
repair hypothesis. Do not spend the entire task rebuilding the test environment.
If no meaningful check can run, record the uncertainty and follow the original
diff-review and submission procedure without claiming validation.

Keep the repair focused on production behavior. Do not modify, remove or weaken
existing tests to manufacture a pass. Scratch diagnostics must not replace the
project's original expectations. After a production change, use fresh relevant
results; tests run only before the change do not validate the current source.
