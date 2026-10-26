# Actual CPU environment

Notebook **141004018/v1**, private, **COMPLETE**. One version executed; no
corrective version was required. Metadata recovered with the official CLI confirms
GPU=false, TPU=false, internet=false, no model or competition input, and one private
dataset input. The code independently found no NVIDIA device nodes. No model was
loaded, and no Gemma request or competition submission occurred.

The already validated PR37 CPU image is reused, not requalified as new Compiler
research: `gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461`.
Actual CPython **3.12.13**, Linux x86_64/glibc2.35. Each task receives a fresh venv
with no system-site-packages, a source import path pointing to its restored archive,
and no bytecode writes. No Docker daemon or Docker-in-Docker is used.

Twenty-five original wheels are bundled with SHA256-pinned requirements and
retained licenses. Installation uses `--no-index --no-deps --require-hashes` and
the mounted wheel directory; `pip check` passes in all three environments.
DEPENDENCY_LOCK.json records publisher URLs, versions, file hashes and license
identities. Installed versions/RECORD hashes are in TASK_REPRODUCTIONS.json.
The main stacks are Django 4.2 source + asgiref3.8.1/sqlparse0.5.3;
xarray base source + numpy1.26.4/pandas2.2.3; FastAPI0.123.2 base source +
starlette0.48.0/pydantic2.11.7/httpx0.28.1/python-multipart0.0.20.

## Observed warnings and scope

The image emits `Error in sitecustomize ... ModuleNotFoundError: ... wrapt` at
Python startup. It is nonfatal: installation, import smoke, pip check and positive
behavioral controls all finish successfully, followed by explicit target failures.
This warning is preserved in the original archive. The startup hook's source was
not captured, so a pristine/hermetic interpreter is **not** established. xarray
also emits an old-source SyntaxWarning. Its dynamic version is `0+unknown` because
the codeload archive lacks Git version metadata; identity comes from commit/archive
and source-tree hashes, not the displayed version string.

The xarray import exposes setuptools' bundled distribution metadata, including
duplicate packaging metadata. These observed names/RECORD hashes are retained,
not silently treated as separately downloaded wheels. The installed setuptools
wheel remains hash-pinned. No claim of equivalence to the benchmark's historical
Docker environment is made. These observations do not prevent the three scoped
checks, but broader regression/environment compatibility is untested.

## Execution, integrity and cleanup

All commands are bounded (venv/import/check/probe 60 seconds, install 180 seconds;
default command 120). Timeout kills and reaps the owned process group on Linux.
The driver has a 2100-second outer timeout and the requested CPU window is 3600.
No task timed out. Task workspaces are deleted only after resolved-path containment
checks. Internal relative archive links are preserved; escaping paths/links and
non-file/device entries are rejected. This is a controlled development driver,
not an adversarial Agent sandbox or a replacement for official chroot isolation.

Actual task wall times: Django **12.203s**, xarray **14.636s**, FastAPI **7.202s**;
sum **34.041s**. Notebook body **37.119s**; last platform conversion-log timestamp
**57.287s**. The latter is not a bill. Billed CPU seconds and an independently
attributable account resource delta are unavailable and remain null.
All three source trees are unchanged and all workspaces/processes are cleaned up.
