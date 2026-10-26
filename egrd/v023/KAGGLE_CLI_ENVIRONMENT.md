# Actual CLI and CPU environment

Starting PR36 HEAD: e11b28c99bec91049aec68119fead5e13fa68373; parent:
765530b39a7666a78ece099756fac925a932c617. PR36 was open, Draft, unmerged.
Branch: feat/egrd-v023-cli-environment-recovery. No historical merge was made.

Installed official CLI: **2.2.2**. Its server warning suggested 2.2.5; no upgrade
was performed. Installed help confirmed kernels list/pull/push/status/logs/files/
output, competition file pagination/download and dataset metadata/files commands.
Authentication succeeded for private owned Notebook listing/metadata and
competition files. No config, token, credential file or signed URL was printed.
The local HTTPS proxy and UTF-8 output were used without changing account settings.

Read-only discovery found the existing CPU03 Notebook and the legitimate
`metric/gemma-4-developer-agent-wheelhouse` dataset. Its metadata, CPU03 pinned
image and previous payload identity were read; old Notebooks were not modified.
All three pages of accessible competition files were obtained (524 total), then
only public tasks.jsonl and HARNESS_README.md were redownloaded. Both hashes match
the old frozen source. Pagination tokens remain private and are redacted from
public CLI records. Raw read/error records are retained by hash.

## Unique CPU dispatch and recovery

`kaggle kernels push -p <cpu-v1> -t 3600` was issued once, after metadata/payload
checks and a durable local dispatch record. No accelerator argument was supplied.
The input metadata explicitly used private=true, enable_gpu=false,
enable_tpu=false, enable_internet=false, machine_shape="", model_sources=[].

The initial requested slug was `wudangdexiaodoashi/egrd-v023-compiler-cpu`.
An owned search found no match; its lookup returned an access/slug error. The
CLI push warned that the title resolves differently and **returned**
`wudangdexiaodoashi/egrd-v023-compiler-cpu-recovery`. A lookup at the intended
slug failed; no repeat save followed. Read-only pull/status at the returned ref
confirmed **140992640/v1**, private CPU, machine_shape="None", no accelerator,
no internet or model input, ultimately COMPLETE. No second version was used.

Actual CPU runtime: Python **3.12.13**; torch reported **0 GPU devices**. The
historical container digest was retained. 41 approved wheels were hash-checked
and installed offline in that ephemeral environment. No weights were loaded.
The complete official execution succeeded, establishing CPU availability for
this run. Account GPU balance was not queried and is not inferred from CPU
success; no CLI resource-balance or isolated billing claim is made.

CLI help and source semantics are documented by the
[official kernels metadata reference](https://github.com/Kaggle/kaggle-cli/blob/main/docs/kernels_metadata.md).
Actual CLI responses/returned metadata, not generic examples, determine the
identity and CPU configuration recorded in KAGGLE_EXECUTION_RECORD.json.
