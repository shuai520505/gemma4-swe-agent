# Final independent integrity check

Frozen origin: PR31 `f8b63e9db3d97760d1798fe12dfd5139871dcdc0`, still
Draft/open/unmerged. PR30/PR32 and all historical candidates/evidence remain
unchanged. This isolated execution branch is Draft PR33, stacked on PR31.

Original A/B/C ZIP SHA256 values:

- A: `07263740c5ee22bf6611d7fa31dafbc84d7fb50288d22355b9201cd6954a6840`
- B: `d962044f264d8f36aea6263abf4dcdb118d5755e82a91cb9b2bd0bc1f6f7c9cd`
- C: `8dd48fee0c96424a40ed47512f0d788d9b13518e7d73395bd89d2fb07204eb83`

The shared ZIP SHA remains
`38170bc0d6684ea09097d106cb0a4fbcf5fbc67a0b7c061f139ae99bccc558b5`.
It contains205registered file pins **plus the registration manifest itself**,
206archive members. Every206member was independently compared with Batch2's
recovered source bytes. The205count in earlier CPU/dispatch records refers to
registered files; generated Python bytecode in the output is not a new frozen
input. No candidate rebuilding or shared production edits occurred.

Batch1 source commit474029fe9f133b1ac9db7721ad7316aa0ae66470;
Batch2 source commita9dea32c86341d16e65b01a921cb4b54f09b274f, from the actual
append-only dispatch claims. Exact outer source/payload/owner/ID/version was
reconciled read-only. API JSON serialization differs in whitespace from the
local Notebook bytes, while parsed source and embedded payload match exactly.
The separate journal UNKNOWN_STOP/HTTP200/recovered-identity facts remain.

Batch2 rehashes all8model/tokenizer/template files against the frozen manifest.
Actual4L4,CUDA12.8,PyTorch2.10.0+cu128,vLLM0.19.1,ADK1.36.1,official library
versions,TP4 and before/after trusted dependency fingerprint match. All actual
generation requests carry16384output,4096thinking,seed17. All compiled
generation configs match. Six official tool schemas match across A/B/C; B/C's
four added Skill tool schemas match each other. Actual Skill script execution
under Gemma is NOT_EXERCISED, not a falsely claimed compatibility pass.

The two frozen task identities were checked in the production entry; both
trusted baselines ran from original snapshots with no candidate patch. Native
TaskResult/JUnit provenance and exact duplicate snapshot teardown pairing were
rechecked; official resolved=false remains unchanged. Distinct contexts, chroot
roots/UIDs and output directories are recorded; first real requests each start
with only system+normal task user input. GPU synthetic isolation canary passes;
all Agent/chroot/native cleanup and model process cleanup pass. No evaluator
overlay was added to Agent input by the unchanged Worker.

Blind review lock precedes native unblinding. Two analysis mistakes were caught
before publication: initial trusted snapshot deployment is not an Agent source
edit; Guard events reside in the Worker journal rather than Agent journal.
The initial derived file SHA
`b9ee5c5b6abaad52f187e4ef3fdb11cc5e7eae3a75af15dc081b279e124cbe58`
is retained in private analysis-initial. Three actual-archive regression tests
now independently verify deployment exclusion, guard rejection and request/Skill
denominators. An initial local console GBK rendering error was corrected with
UTF8; no execution evidence changed. No failure was rewritten as PASS.

`RAW_ARCHIVES.json` binds original private outputs by bytes/SHA/CRC. Public
reports contain derived measurements and identifiers only. Raw Issue text,
model/tool trajectories, actual patches, JUnit/test bodies, signed URLs and
credentials stay outside Git. `INTEGRITY_MANIFEST.json` binds the safe delivery;
it excludes itself and Python cache files, not frozen history.
