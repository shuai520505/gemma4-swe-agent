# CPU02 existing-resource read-only recovery

This independently authorized study reads the existing Notebook ID140021966/version1 associated with the CPU02 save at2026-10-21T12:40:52UTC. Base PR14/source c454be36ff00663257b6bf4cf7067e151ae4c8b6. It never invokes launch.py or modifies original execution events. This user grant authorizes only read queries and already-generated output download. No SaveKernel/restart/new version/CPU03/GPU/model/Agent/Submission is allowed. Existing CPU01 and CPU02 UNKNOWN_STOP snapshots remain immutable.

Run the unit tests before `python -m u_re.v01.experiments.fastapi_pilot_01.attempts.cpu02.reconciliation_01.recover`. The latter refuses an existing evidence directory. Mock tests do not prove official CPU task admission.

Latest result: **IDENTITY_CONFIRMED / RUN_COMPLETE / CPU_TASK_ADMISSION_BLOCKED**. Read FINAL_DECISION.md for Q1-Q12 and CPU_ADMISSION_REPORT.md for the actual one-task collection failure. The recovery made16read-only requests and no save/run request.
