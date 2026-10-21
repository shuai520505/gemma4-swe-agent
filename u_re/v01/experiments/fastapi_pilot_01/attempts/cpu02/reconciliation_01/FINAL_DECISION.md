# Final Q1-Q12 and gates

| Question | Evidence-based answer | Evidence |
|---|---|---|
|Q1.NumericID lookup?|Installed SDK has no direct numeric-ID GetKernel. Exact latest owner/slug read returnedID140021966;numericID is therefore confirmed indirectly by supported API.|SDK_READ_AUDIT.md;RESOURCE_IDENTITY.json|
|Q2.Actual owner/slug/ref?|ownerwudangdexiaodoashi from fullref;sluggemma4-u-re-fastapi-pilot01-cpu02;refwudangdexiaodoashi/gemma4-u-re-fastapi-pilot01-cpu02. author is a display name.|RESOURCE_IDENTITY.json;OWNER_FIELD_ADDENDUM.md|
|Q3.Identity consistent?|Yes:IDENTITY_CONFIRMED,actualID/ref/slug/private/version/flags/source/payload cross-checks. Original UNKNOWN_STOP preserved.|evidence_confirmed/RESOURCE_IDENTITY.json;HISTORY_AUDIT_AFTER.json|
|Q4.Version1 exists?|Yes,current_version_number1 checked repeatedly before/after output. Optional versionLabel1 alone returned404 and is not used as proof.|evidence_confirmed/LATEST_BEFORE_STATUS.json;LATEST_BEFORE_DOWNLOAD.json;LATEST_AFTER_DOWNLOAD.json|
|Q5.Source matches?|ByteSHA differs due serialization;complete Notebook JSON equality and embedded payload equality true. No claim of raw byte equality.|SOURCE_IDENTITY.md;evidence_confirmed/platform_source.ipynb|
|Q6.Actually ran?|Yes,Kaggle COMPLETE,Notebook log contains CPU02executionID,SCREEN_CPU_EXIT0 and archive export;native evidence exists. No reliable platform start/end timestamps supplied.|RUN_STATUS.json;evidence_confirmed/output/notebook.log|
|Q7.Output downloaded?|Yes,639366-byte ZIP,CRC valid,258manifest entries verified,186source members exact. ZIP SHA3689eb29a70ca8309172f036a3f50a0921868c8527100a699b509ede2a55bf1f.|OUTPUT_MANIFEST.json;ARCHIVE_AUDIT.json|
|Q8.RealJUnit/TaskResult?|Yes,captured before sandbox cleanup;nativeexit2,JUnit3collectionerrors;consistent counts/exit.|native_evidence/validation/01-fastapi_14262/;ARCHIVE_AUDIT.json|
|Q9.How many baselines/admitted?|1entered:first frozen taskfastapi_14262,0eligible. Scopekeyword errors2 and missinginline_snapshot1;remaining49NOT_RUN. No Agentfailure inference.|TASK_SCREENING_LEDGER.json;CPU_ADMISSION_REPORT.md|
|Q10.Candidates/exclusions/rank unchanged?|Yes,both fullZIP/member pins and all inherited files match.79exclusions/50rank unchanged.|HISTORY_AUDIT_AFTER.json;FROZEN_HISTORY_BEFORE.json|
|Q11.Zero new execution?|Yes,16read-onlyHTTP,zeroSaveKernel/rerun/GPU/Gemma/Agent/Submission. OldSavecount remains1.|READONLY_QUERY_LEDGER.json;immutable prior execution/events/|
|Q12.Two tasks/GPU next?|No,CPU_TASK_ADMISSION_BLOCKED. Need separately reviewed environment/evidence work and separate compute authorization;GPU must remain unstarted.|CPU_ADMISSION_REPORT.md;RECOVERY_STATE_ASSESSMENT.md|

Read-only recovery:GO(completed). CPU task admission:NO-GO. GPU resource admission:NOT_EVALUATED. GPU execution:NOT_AUTHORIZED. U-RE algorithm benefit:GPU_NOT_TESTED. All artifact SHA256s,including raw JUnit/TaskResult/source,are indexed in INTEGRITY_MANIFEST.json. No reference repair was downloaded or used. No historical evidence/candidate was changed.
