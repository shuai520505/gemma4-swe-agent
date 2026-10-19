# T500 single-factor candidate change

Parent: c979394af8521ed62d9fcca990a260d715f1042c; frozen S2-300 ZIP SHA256 1f9345cc11362acfc19fbede48284aa934dfbe3a36fe0aa889134125fa8de807.

Exactly one member changes: eval_config.yaml max_time_minutes5.0 becomes8.333333333333334. In IEEE754 Python arithmetic this value times60 is500.00000000000006; native wall-clock overhead is independently tested. agent.yaml, Main Prompt, EGV Prompt and child YAML are byte-identical to S2-300. No model/tool/generation/seed/delegation-policy change.500 seconds are shared across Main and EGV, not separately allocated. Official Stage1 parser validation and actual native deadline are separate gates.

New candidate ZIP SHA256: 13968b67844d1041bfb79b9f11fc21ae66fb36aee5b00d3b91c526d5d35da329

CPU01 upload was rejected before execution because the Notebook exceeded Kaggle's1MB source limit. Its bytes and rejection are retained. CPU02 removes unrelated archival metadata from the CPU payload; no candidate member changes. CPU model responses are scripted; tool edits/assertions/submission remain real.
