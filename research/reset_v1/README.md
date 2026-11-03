# GEMMA RESEARCH RESET V1

Start with [FINAL_RESEARCH_REPORT.md](FINAL_RESEARCH_REPORT.md) or the offline filterable [RESULTS_BOARD.html](RESULTS_BOARD.html). All eleven requested research outputs are in this directory. No agent/runtime/evaluator package is changed.

Reproduce local analysis from the original listed archive paths:

```powershell
python research/reset_v1/audit_history.py
python research/reset_v1/finalize_audit.py
python research/reset_v1/build_board.py
python -m unittest discover -s research/reset_v1 -p test_audit.py -v
```

The audit intentionally depends on original local raw archives, including read-only recovered Kaggle outputs. `ARCHIVE_PROVENANCE.json` locks every inspected archive and deduplicated alias. Raw ZIPs are preserved locally under `raw_recovered/`; they are not republished in this research commit. Source paths outside this repository require access to those retained originals. Derived artifacts alone do not replace raw evidence.

Compiler-only reproducibility uses the existing frozen SDK environment:

```powershell
work/r2-audit/sdk-env/Scripts/python.exe -X utf8 research/reset_v1/compile_parity.py
```

It performs no HTTP/model request. Official Compiler code is unchanged; the public generation-constraints parameter supplies prospective common defaults to both immutable ZIPs. Full Linux Native acceptance is separate and currently blocked. No Notebook dispatch command is included.

Unknown semantic labels remain UNKNOWN. Only the five EGRD-related/control traces received manual semantic review in this audit; other sessions have raw action/outcome inventories, not fabricated causal adjudications. Dashboard Native booleans are explicitly raw. The proposed cohort is only task/Issue-locked until snapshot hashes are materialized before execution.
