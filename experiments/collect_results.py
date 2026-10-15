"""Audit downloaded real pilot outputs; no synthetic or missing inference results."""
import argparse
import hashlib
import json
from pathlib import Path
from statistics import mean
import zipfile

from experiments.metrics import summarize
from experiments.prepare import ROOT, verify_frozen, write_new


def collect(directory):
    directory = Path(directory)
    summaries = list(directory.rglob('comparison_status.json'))
    if len(summaries) != 1:
        exceptions = list(directory.rglob('exception.json'))
        raise ValueError(f'Expected one real comparison status; found {len(summaries)}; exceptions={exceptions}')
    run = summaries[0].parent
    registered = json.loads((ROOT / 'experiments/preregistered.json').read_text())
    actual_plan = json.loads((run / 'registered_plan.json').read_text())
    if actual_plan != registered:
        raise ValueError('Actual plan differs from preregistration')
    for name, digest in registered['source_hashes'].items():
        if hashlib.sha256((run / 'arms' / name).read_bytes()).hexdigest() != digest:
            raise ValueError(f'Actual arm source differs from frozen input: {name}')
    records = json.loads((run / 'comparison_records.json').read_text())
    by_order = {r['index']: r for r in registered['schedule']}
    if len({r['order'] for r in records}) != len(records):
        raise ValueError('Duplicate run order')
    for row in records:
        planned = by_order[row['order']]
        if any(row[k] != planned[k] for k in ('arm', 'instance_id', 'base_commit')):
            raise ValueError('Observed run identity differs from registration')
    summary = summarize(records, registered['schedule'])
    if summary != json.loads((run / 'comparison_summary.json').read_text()):
        raise ValueError('Recomputed metrics differ from native summary')
    treatments = []
    for row in records:
        trace = run / 'runs' / Path(row['run_directory']).name / 'trace_legacy.json'
        check = dict(order=row['order'], arm=row['arm'], trace_present=trace.exists(),
                     prompt_matches=None, observed_models=[])
        if trace.exists():
            entries = json.loads(trace.read_text(encoding='utf-8'))['entries']
            expected_prompt = (ROOT / 'candidates' / row['arm'] / 'submission/prompts/system.md').read_text(encoding='utf-8')
            prompts = [e.get('content', '') for e in entries if e['type'] == 'system_instruction']
            # The real V0 trace strips the include file's trailing newline.
            # Preserve raw source hashes; normalize only newlines/outer whitespace here.
            check['prompt_matches'] = expected_prompt.strip() in [p.strip() for p in prompts]
            check['observed_models'] = sorted({e['model'] for e in entries if e.get('model')})
            check['required_model_only'] = bool(check['observed_models']) and all(
                'gemma-4-31b-it-qat-w4a16-ct' in m and m.endswith('/2') for m in check['observed_models'])
        treatments.append(check)
    archive = run.with_suffix('.zip')
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None:
            raise ValueError('Evidence ZIP CRC failure')
        for info in z.infolist():
            if not info.is_dir() and z.read(info) != (run / info.filename).read_bytes():
                raise ValueError(f'Download differs from original evidence ZIP: {info.filename}')
    for arm in ('v0', 'v1'):
        rows = [r for r in records if r['arm'] == arm]
        tokens = [r['prompt_tokens'] + r['completion_tokens'] for r in rows if 'prompt_tokens' in r and 'completion_tokens' in r]
        summary['arms'][arm]['mean_observed_total_tokens'] = mean(tokens) if tokens else None
        summary['arms'][arm]['token_observed_runs'] = len(tokens)
        summary['arms'][arm]['official_error_runs'] = sum(bool(r.get('error')) for r in rows)
    report = dict(run_id=run.name, status=json.loads(summaries[0].read_text()), summary=summary,
        kernel='wudangdexiaodoashi/gemma4-v1-paired-pilot', kernel_version=1,
        local_original_evidence_directory=str(run.resolve()),
        evidence_zip_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
        plan_sha256=hashlib.sha256((run / 'registered_plan.json').read_bytes()).hexdigest(),
        original_v0_files_unchanged=verify_frozen(), competition_score=None)
    report['treatment_checks'] = treatments
    report['prompt_normalization'] = 'Universal newlines and outer whitespace only; raw input hashes are checked separately'
    report['treatment_integrity_confirmed'] = bool(treatments) and all(
        c.get('prompt_matches') is True and c.get('required_model_only') is True for c in treatments)
    report['completed_trace_treatment_checks_passed'] = all(
        c.get('prompt_matches') is True and c.get('required_model_only') is True
        for c in treatments if c['trace_present']) and any(c['trace_present'] for c in treatments)
    report['missing_trace_orders'] = [c['order'] for c in treatments if not c['trace_present']]
    target = ROOT / 'experiments/results/pilot-01'
    manifest = {p.relative_to(directory).as_posix(): dict(
        bytes=p.stat().st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest())
        for p in sorted(directory.rglob('*')) if p.is_file()}
    write_new(target / 'download_manifest.json', (json.dumps(manifest, indent=2) + '\n').encode())
    write_new(target / 'raw_comparison_records.json', (run / 'comparison_records.json').read_bytes())
    write_new(target / 'result_audit.json', (json.dumps(report, indent=2) + '\n').encode())
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('directory', type=Path)
    args = p.parse_args()
    print(json.dumps(collect(args.directory), indent=2))
