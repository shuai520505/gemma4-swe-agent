# Frozen S2-T300 official submission preparation

User requested one official300-second S2 submission after T500. Current daily API limits:numToday1,numAllowedNow0,numTotal2. No T300 formal request was sent;Submission ID=null. Existing T500 ID57402336 remains PENDING at the recorded check. A new UTC day is expected at2026-10-20 00:00UTC(08:00 Asia/Shanghai);fresh limits/entry/duplicate checks are mandatory then. No automatic delayed submission is scheduled.

Packaging-only Notebook wudangdexiaodoashi/gemma4-s2-t300-first-official-score saved version1 is COMPLETE. Downloaded submission.zip is byte-identical to frozen S2-EGV-AgentTool-V0.1 ZIP1f9345cc11362acfc19fbede48284aa934dfbe3a36fe0aa889134125fa8de807. Root agent.yaml,five members,CRC passed. Main/EGV500s candidate is not substituted: this is original shared300s/60 counted tools,120s command,31B/output16384/thinking4096/seed17. The original source ZIP/Prompts and all T500 evidence remain unchanged.

Before submission:run preflight.py;require numAllowedNow>=1,entry enabled,no already accepted matching T300 submission;verify output/candidate hashes again. Submit saved version1 exactly once. If creation response is ambiguous,query official submissions before any retry;never duplicate. Prepared CLI shape (NOT EXECUTED):

    kaggle competitions submit gemma-4-developer-agent -k wudangdexiaodoashi/gemma4-s2-t300-first-official-score -v 1 -f submission.zip -m "S2 EGV AgentTool T300 first official score"

No research GPU,LoRA,new Prompt,candidate modification or account switching. A saved Notebook is not a formal scoring submission. API preflight snapshots and downloaded packaging result/log/ZIP are in evidence/;SUBMISSION_RECORD.json explicitly records NOT_RUN and zero formal requests.
