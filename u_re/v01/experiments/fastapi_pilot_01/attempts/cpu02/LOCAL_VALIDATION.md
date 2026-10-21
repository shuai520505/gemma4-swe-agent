# Local test evidence and limits

Command:python -m unittest u_re.v01.experiments.fastapi_pilot_01.attempts.cpu02.tests.test_dispatch u_re.v01.experiments.fastapi_pilot_01.attempts.cpu02.tests.test_preparation -v

Final20/20PASS,release check4.304s,evidence/release_local_tests.log (earlier20pass retained atfinal_local_tests.log). Uses actual installed kagglesdk typed requests,HTTP serialization and response/error parsing;only outer requests.Session.send transport is replaced. All SaveKernel interactions in tests are local mocks;no real Kaggle Save/GPU/Agent/native task. Tests cover JSON200,non-JSON502,empty204,403,429,timeout,disconnect,disk observer failure,child os._exit afterdispatch before response,restart,wrong/existing slug,redaction,missing grant,GPU/TPU/model/network flags,second SDK send,torn claim,unexpected accepted version,payload/config/collector guards. Exact API retries0 and redirectsfalse are asserted in fake transport. Real launch with missing grant is run in a child process with any network forbidden and fails before SDKwork.

First14-method run failed11 before mocked transport due duplicate at_utc keyword in journal.append;fixed by distinct event_at_utc. Original source/failure log retained in evidence/dispatch_v00.py.txt,fault_tests_01.log andFAULT_FIX_HISTORY.json. Next14pass and expanded18pass retained. No failed real task or Save was hidden/retried.

Live collector/official Linux baseline compatibility isNOT_RUN. Controller is a research upload safety layer,not part of candidateZIP/official Agent tools. Existing six tools and official Verifier are untouched. No CPU02 authorization file is present. Future launch source must match sealed file hashes;do not overwrite frozen artifacts to force a pass.
