# Pinned dependency recovery

Priority 1 was checked: the local interpreter still lacks the complete pinned
SDK, and PR36's five cached SDK wheels do not form a complete local dependency
closure. No local SDK upgrade, installation or substitution was attempted.

Priority 2 succeeded using the historical trusted Kaggle CPU image and original
wheelhouse. The complete **41-wheel** set matched the inherited manifest before
installation. The inherited installer used no-index/no-deps force-reinstall in
the disposable CPU environment, excluded cutlass, normalized inherited wheel
link names, and retained installation logs. No internet or PyPI resolver was
used. No GPU/model service was started.

Actual imported distributions:

| Distribution | Version |
| --- | --- |
| swegemma | 0.2.11 |
| adk-submission | 0.2.13 |
| google-adk | 1.36.1 |
| adk-eval-core | 0.1.0 |

Whole distribution hashes match meer/v01/OFFICIAL_SOURCE_PINS.json. Eight
previously pinned installed source members were also byte-checked. Compiler,
callback resolver, official Runner and SkillToolset source identities are
archived. RECOVERED_DEPENDENCY_IDENTITIES records actual wheel/source digests
and image identity. There is no claim that every optional cloud integration
has been exercised, or that the recovered Linux environment is a local Windows
installation.

The native trusted synthetic verifier emitted an ensurepip-unavailable warning
and used its existing no-pip fallback. Both targeted synthetic tests actually
executed and passed; this warning is preserved, not concealed or scored as an
Agent failure. SDK experimental-Skill warnings are also retained. No trusted
test, verifier or callback registry was modified to make acceptance pass.
