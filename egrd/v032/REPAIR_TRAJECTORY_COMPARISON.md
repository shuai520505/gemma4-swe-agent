# Observed repair trajectories

| Observation | A: original Issue | B: Issue + frozen receipt |
|---|---:|---:|
| First relevant source-read call |15.596s|14.145s|
| First production edit observed |291.116s|null: none|
| Production files changed |django/contrib/auth/forms.py|none|
| Agent command errors |7|4|
| Production post-edit checks |0|N/A|
| Successful explicit submission |false|false|
| Stop |300s native Agent deadline|277.611s server context admission|

Times for calls are observed ADK event times relative to the session-start journal;
edit time is the post-action source observer's recorded Agent elapsed time.
They are not inferred internal reasoning timestamps. See DERIVED_TRAJECTORY_METRICS
for event indices and private trace references.

A inspected relevant implementation early, wrote scratch/test material, then
encountered a missing test directory, nonexistent root manage.py, missing pytest
executable/module, missing distutils, missing django-admin and unconfigured test
settings. Six test-command attempts failed before establishing a target assertion.
It made a plausible production edit only at291s and spent its remaining time on
an in-flight model request canceled at the official deadline. No fresh behavioral
verification or submission followed.

B inspected the auth form and ModelForm save path by30s, drafted scratch code,
read existing tests and a ManyToMany fixture, then added an Agent-written targeted
test. It did not modify production code. It tried a nonexistent manage.py, missing
pytest executable/module and finally an invalid test-label path. The resulting
traceback entered history before the next generation was rejected. No successful
Agent-side discriminating check was observed in either arm. Static assertion
presence in a test is not successful execution or proof of Issue relevance.

Continued source investigation was related to the Issue; it is not all labeled
waste. The demonstrably ineffective actions are the actual failing test-entry
attempts. Missing tools/dependencies are an Agent-visible development-environment
limitation, separate from the genuine target failure reproduced by the trusted
owned probe. This environment did not provide the full Django test dependency
suite. No recommendation assumes an earlier edit was already known correct.

The receipt was present exactly once at B's real model boundary. B's targeted
test attempt is compatible with that contract, but the original Issue also
describes it: receipt-caused understanding or behavior cannot be independently
identified from this one pair. A/B are development-exposed, fixed order, one seed
stream and one execution each; this is not held-out generalization evidence.
