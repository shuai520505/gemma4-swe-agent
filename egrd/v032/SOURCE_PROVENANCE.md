# Source provenance and limits

PR40 was independently re-read through GitHub: open, draft, unmerged; head
`d2a09cb114df4621885f437bf04c4b7d919d47de`, branch
`feat/egrd-v0311-cpu-runner-recovery`. This branch is stacked on that exact commit.
No historical PR was merged. Candidate/member and PR39/40 manifest/archive
hashes are independently rechecked by `prepare.verify_history()`.

The known successful real-model serving source is
`u_re/v01/experiments/action_priority_01/real_gemma_abba03/session.py`; model
asset pins are from
`u_re/v01/experiments/gemma_smoke_01/MODEL_RUNTIME_CONFIG.json` and repeated
historical runs. Only the serving/lifecycle path is reused. Its seed17,
FastAPI task logic and later research Guard are not inherited.

The exact pinned `adk_submission-0.2.13` wheel's `VllmConfig` dataclass fields
are checked by offline AST against the proposed settings. SDK source pins are
in `egrd/v023/RECOVERED_DEPENDENCY_IDENTITIES.json`; the previous full CPU run,
its 17 gates, CRC and all 353 archived evidence files are independently checked.
This is not a new full-Compiler execution in the current local environment.

Official serving source reviewed at vLLM tag **v0.19.1**:

- [arg_utils.py](https://github.com/vllm-project/vllm/blob/v0.19.1/vllm/engine/arg_utils.py):
  lines310 and997 use `argparse.BooleanOptionalAction` for the prefix-cache flag.
  `--no-enable-prefix-caching` is a shared experimental setting, not a claimed
  historical S0 setting.
- [tokenize/protocol.py](https://github.com/vllm-project/vllm/blob/v0.19.1/vllm/entrypoints/serve/tokenize/protocol.py):
  `TokenizeChatRequest` accepts model/messages/tools/chat-template arguments;
  `TokenizeResponse` reports count and max_model_len. No inference is needed to
  measure both exact expected initial inputs before Session A.
- [tokenize/serving.py](https://github.com/vllm-project/vllm/blob/v0.19.1/vllm/entrypoints/serve/tokenize/serving.py):
  tokenization uses the server renderer and reports the actual model limit.

Downloaded source-file hashes are retained in INTEGRITY_MANIFEST.json. A first
attempt to read the obsolete `entrypoints/openai/serving_tokenization.py` URL
returned404; the official tag's tree resolved the current path. This was source
research, not a package change or an inference attempt.

The installed CLI2.2.2's quota `to_json()` loses duration days and emits malformed
fractional seconds. Raw serialization is preserved privately; canonical quota
values use its parsed timedelta days/seconds/microseconds. No upgrade was made.
The first refreshed job-status read failed404; a subsequent bounded read-only
check preserved all ten results, including null/error and QUEUED. Neither error
was converted into an inactive-job claim. New-job metadata was read only to
classify accelerator allocation intent; its code is not used by this experiment.

All private raw task/input, model-boundary and evaluation data remains outside
Git. No trusted test, reference solution, hidden material or model reasoning is
included in these public reports. The public competition input is only the
historically established host-side L4 environment mount; no files are read or
staged from it. The Agent chroot has no Kaggle input mount. Actual dynamic
isolation tests and model bytes must still be observed if a future dispatch runs.
