# Local validation and reproduction

Local command (Windows Python3.11.9, no Kaggle/model calls in these tests):

```powershell
python -m unittest u_re.v01.experiments.fastapi_pilot_01.tests.test_policy u_re.v01.experiments.fastapi_pilot_01.tests.test_readiness -v
python -m u_re.v01.experiments.fastapi_pilot_01.seal
```

Final local suite14/14 methods PASS in9.948s; see evidence/final_local_tests.log. Six prospective tests passed before protocol commit77ad023. These verify byte-preserved exclusions/rank/candidates,structured decision rules,GPU STOP,redaction,non-JSON/empty response handling,no-retry guard,unconfirmed outcome nulls,auth-vs-admission distinction,precommitted source and5747 inherited hashes,SDK wire Notebook identity. A fake SDK import is used only to test the host refusal before any API mutation; it does not validate official Runner or Linux baseline behavior. Response502/204 fixtures are local observer unit tests,not claimed Kaggle responses.

Official baseline artifacts are absent;accepted Notebook version and actual platform execution remain unknown. Do not run cpu_host launch again:an existing attempt directory intentionally refuses saves. Do not regenerate/overwrite this frozen Notebook/build under the same identity. First reconcile the existing slug through authoritative platform evidence;collect existing output if any. No automated retry or second Notebook is authorized by this blocked-state script.

register.py is the prospective one-time builder pinned to PR11 head;it refuses later HEAD and existing different files. prepare_cpu.py freezes the77ad023 sources and approved inherited CPU runtime;metadata enable_gpu/enable_tpu/internet=false,model_sources empty. CPU build commit e6db9ac predates dispatch. auth_diagnose.py has an exclusive receipt and blocks credential mutation;do not rerun it just to overwrite AUTH_STATUS.json. Initial host source is preserved separately,while current host includes an unused-for-retry non-masking observer fix.

The seal checks every new non-cache byte,5747 inherited files,ZIP CRC/member pins and currently known credential values without recording them. Manifest excludes itself,caches,_local and download. Source/log/evidence bytes are preserved by local .gitattributes. Independent checks do not require a GPU or Kaggle credentials,except the optional in-memory credential-leak comparison uses present local sources without network.
