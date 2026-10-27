# Captured official-model boundary: PASS

Both arms use the same original S0 ZIP, unchanged source snapshot, official
Compiler/Runner and six-tool schemas. Independent contexts and loopback scripted
servers receive 11 HTTP requests each. Every body is persisted immediately when
received, before replying; finalization also saves the accumulated list even if
the Session fails. Full initial and subsequent bodies remain private.

Independent collection reparses the raw initial bodies and removes exactly one
frozen observation suffix from B. The resulting complete parsed request equals A.
Only the top-level `messages` field differs before removal. System instruction,
model, tools, remaining parameters, message ordering and roles match. Both initial
requests have roles `system`, `user`; no previous arm history is present.

| Surface | A | B |
|---|---:|---:|
| Frozen task input UTF-8 bytes | 559 | 2134 |
| Raw HTTP body bytes | 13612 | 15269 |
| Frozen evidence supplement present | No | Yes, exactly once |
| Captured scripted requests | 11 | 11 |

The task supplement is 1575 bytes; its JSON-encoded HTTP body overhead is 1657
bytes. Neither number is a token count. No exact tokenizer/template is available;
rendered token overhead is **UNKNOWN/null**. Fabricated scripted usage fields are
not treated as actual prompt/completion/received tokens.

Raw initial request SHA256:

- A: `bd8d362f776a6fc38756e4a01f51134df2dbb2c8ba08cb2b051110323f29b3df`
- B: `7baed97fb0d5363d22cd197f4e10e1a29296e3b2219b78e1f505dc4069accad2`

The original Issue is preserved verbatim in both. B receives exactly the PR39
observation; no receipt/probe file is placed in either workspace. The public
receipt is not copied into this new namespace. No reference patch, answer column,
trusted probe program or overlay enters either request.

Actual parameters in both: model label `gemma-4-31b-it-qat-w4a16-ct`,
`max_completion_tokens=16384`, `thinking_token_budget=4096`,
`chat_template_kwargs.enable_thinking=true`. Seed, temperature and top_p are
omitted, not silently set to 17 or zero. This endpoint runs SCRIPTED_ONLY, not
Gemma inference. The compiled generation records match exactly.

The frozen original prompt member contains 13 CRLFs. Native text loading
normalizes them to LF identically in both arms: original member SHA is preserved,
while compiled instruction SHA is
`04ec91bdecda3d50e78b56bd3b33547d531fbc4b59c1809c4380b52cbb7ce6df`.
An initial collector compared raw bytes directly to the compiled text hash and
correctly stopped. It was corrected to account for native newline handling;
runtime/candidate bytes were not changed and no Notebook rerun occurred.

The first-request comparison isolates input construction. Later histories contain
ordinary timing/status/output differences and are not claimed byte-identical.
No custom Context Guard, compaction, callback or thought-filter policy is added.
This proves evidence availability at the boundary, not autonomous Gemma use.
