# Final GPU gate

`R12_RESOURCE_BLOCKED` — CPU integration is PASS; dispatch remains blocked by unconfirmed current four-L4 capacity and incomplete job visibility.

| Required answer | Evidence / conclusion |
|---|---|
| End-to-end CPU simulation | PASS; native tools, production edit, patch retention, independent verifier, HTTP/ADK evidence and cleanup exercised. CPU sentinel outcomes are not repair evidence. |
| Nine assemblies | Identical frozen task/order/configuration; all nine compared and dispatch inputs rematerialized. |
| Candidate hashes | All original BASELINE/R1/R2 ZIP and member hashes retained; no R3. |
| GPU quota | 30.0000 available quota-hours after reservations at 2026-10-31T03:32:15.108089+00:00; frozen 20.3333-hour numeric floor PASS. |
| Four L4s | CAPACITY_UNVERIFIED; supported type and past success do not prove current allocatable capacity. |
| Platform window | Documented 12-hour CPU/GPU session limit accommodates frozen 5 hours; actual allocation/dispatch was not attempted. |
| Cost / stopping | 72-minute total Agent cap; expected 1.5–2 node-hours = 6–8 physical L4-hours = 3–4 Kaggle quota-hours. Maximum 5 node-hours = 20 physical L4-hours = 10 quota-hours at the published 2× rate. Keep original 20.3333 quota-hour admission floor. Ordinary repair failures continue; infrastructure/trust/backend/evidence/cleanup failures stop, suffix NOT_RUN; no selective reruns. |
| Enter real GPU execution | NO. No GPU Notebook, real Gemma inference, R3 or competition submission was started. Explicit new human GPU authorization is still required even after a future READY gate. |

The current bounded status scan checked 232 identifiable notebook refs; 60 remain UNKNOWN, plus 1 unidentified private row. 0 running/queued records were observed in that scan; this does not certify that no conflicting jobs exist. Other jobs were not modified. Source timestamps, quota reservations, status counts and raw-evidence hashes are in RESOURCE_READINESS.json. Read-only interfaces cannot reserve or prove real-time four-L4 capacity.

Budget units were corrected with auditable primary evidence: the [competition overview](https://www.kaggle.com/competitions/gemma-4-developer-agent/overview) states 2× ordinary-machine quota consumption for L4×4. Physical device-hours are a different unit. The numeric launch threshold and research design remain unchanged. The [Notebook documentation](https://www.kaggle.com/docs/notebooks) lists the 12-hour runtime limit. Both sources checked 2026-10-31T03:34:01.017917+00:00.

The 900-second former 'repeat Issue acceptance' allocation is retained as a conservative hash/receipt validation reserve; no completed Issue acceptance is rerun. The full worst-case allocation remains 16500 seconds within 18000 seconds. Preparing/mounting, all nine sessions, trusted evaluation, archive and cleanup share that bound.

Next GPU operation, only after fresh capacity/job evidence and explicit human authorization: one offline, pinned-image 4-L4 Notebook, one server, frozen nine-session order, 18000-second window, no retries and no submission. The prepared entry is in GPU_DISPATCH_PACKAGE_MANIFEST.json and currently rejects this blocked gate. No reduced/cohort-swapped alternative is authorized.
