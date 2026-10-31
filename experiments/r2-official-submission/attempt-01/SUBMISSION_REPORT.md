# Frozen R2 — first authorized formal submission

Kaggle accepted one direct ZIP submission: **57843305**. Current observed status: **PENDING** at 2026-10-31T15:42:54.222918+00:00. Public Score: **UNKNOWN / not returned**. Acceptance is not scoring completion or proof of repair success.

The user authorized submission with: “我觉得我们可以先把目前最好的先打包提交一下”. This supersedes the earlier audit-only prohibition for this single formal submission. Historical audits remain unchanged; the previous R2_BLOCKED_BY_BUDGET finding is not rewritten as READY. Hidden workload coverage, official timing and generalization remain unknown and are now subject to actual official scoring.

The uploaded submission.zip is a byte-identical copy of the frozen R2 candidate, SHA256 `af918c1a65aeb211298f13a69b5b789ae6b086974922c80469df87d902eb98d5`, 3646 bytes. Root agent.yaml, includes and four member hashes match the previous genuine official CPU Compiler PASS. No repacking, prompt/config/budget/model changes, R1 merge, Candidate A or R3 is included. Baseline and all 74 protected historical assets rehash unchanged.

Fresh authenticated Kaggle API preflight confirmed the team had entered, direct upload was enabled, deadline had not passed, no same-R2 marker existed in the returned submission history and one submission remained. After acceptance the API reported today's count 1 and remaining allowance 0. These are team submission counts, not GPU quotas. No unrelated job or submission was modified.

Only one explicit competition_submit call was made. A persistent exclusive attempt marker prevents local re-dispatch even if a response becomes uncertain. Subsequent get_submission/submission-limit calls are status reads only. No SaveKernel, new Notebook, local Gemma inference or local GPU allocation occurred. The competition's own scoring lifecycle is separate and not claimed to be GPU-free.

The previous best observed Public Score stays 0.15 until this submission returns an actual score. A missing score is null/UNKNOWN. Pending status cannot be used as Native Resolved, a hidden-task success count, a regression or a score improvement. Later scoring updates must preserve this original acceptance receipt and the original R12/audit evidence.

[Official submission page](https://www.kaggle.com/competitions/gemma-4-developer-agent/submissions) · [Official competition](https://www.kaggle.com/competitions/gemma-4-developer-agent)
