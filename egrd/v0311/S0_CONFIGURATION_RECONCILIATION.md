# Three configuration levels

**HISTORICAL_SERVING_EQUIVALENCE_UNVERIFIED.** Engineering acceptance of identical
A/B compilation is different from reconstructing the historical scoring server.

1. **Frozen package.** `candidates/s0/submission.zip` is the original 1,908-byte
   package, SHA256 `3303d6e1dd246d3861910701beb580c8d9a165ea1eb1c1a13d8c8ba9d6efd4f9`.
   Its Agent YAML declares no generation overrides, seed, thought filtering,
   custom callback, Skill, compactor or research Context Guard. Its budget file
   declares 5 minutes, 60 charged tools and a 120-second command timeout.
   `egrd/v031/S0_AGENT_LOCK.json` binds all member hashes and original score record.
2. **Pinned official Compiler.** The shared CPU path uses unchanged official
   `swegemma 0.2.11`, `adk-submission 0.2.13`, `google-adk 1.36.1` and
   `adk-eval-core 0.1.0`, with the previously frozen wheel/source identities.
   `swegemma.config.build_submission_limits` supplies the default generation
   constraints; PR39 records expected output 16384 and thinking 4096. In
   `adk_submission/schema.py:169-170,207-212`, unset thinking flags/seed remain
   optional. `resolvers/generation.py:364-458` maps configured values into the
   model request. Actual new-run configuration/request captures, when reached,
   are authoritative; earlier CPU results do not fill missing observations.
3. **Future serving.** A future real-Gemma deployment needs separately recorded
   model/tokenizer/template identities, server context and admission policy,
   seed and other server defaults. No seed 17, 15360-input Guard, 1024 reserve,
   output-cap change or thought-filter intervention is silently inserted here.
   The candidate remains unchanged. A/B equivalence within this research runtime
   would not prove equivalence with submission 57261002's unavailable server state.

The CPU model route is loopback SCRIPTED_ONLY HTTP, not a Gemma backend. Its
fabricated usage counters are not model token measurements. No exact tokenizer
or chat template is mounted; rendered token overhead remains null/UNKNOWN.

The Task input supplement is a **research host intervention**, not a capability
claimed for a submitted competition Agent. The exposed Django task supports a
development-only comparison. Native Resolved and canonical SWE-bench resolved
remain null. Synthetic `.git` metadata changes Django's displayed development
version without changing its original source bytes. Ordinary workspace test
configuration prepared by the native Runner is not a production repair.
