# Host-only response observation correction

Initial e6db9ac observer parsed JSON while constructing the save receipt. For a non-JSON response that throws before status is recorded and replaces the downstream SDK result/error. The old source/actual exception chain are retained. Original HTTP status/body cannot be recovered and are left null.

New response_observer.py captures timestamp/status/content-type/byte-count first;non-JSON marks json_response=false without throwing. It never copies arbitrary body/headers/cookies;whitelisted version/id/status only. Recorder file-write failure cannot change the SDK's original response/error path. cpu_host now always restores Session.send in finally. Local tests cover non-JSON502,empty204,JSON200,credential field exclusion and file-write failure. These are host regression fixtures,not Kaggle baseline results.

This correction was NOT deployed into a re-save/retry of this study. Frozen CPU Notebook,payload,rank,protocol and candidate bytes remain identical. Old host source is preserved and all actual Save evidence refers to it. Existing output-directory guard prevents another launch under cpu01. No second CPU request,hotfix into a running Notebook or GPU work occurred.
