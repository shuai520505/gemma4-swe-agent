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
    records = json.loads((run / 'comparison_records.json').read_text())
    summary = summarize(records, registered['schedule'])
    treatments = []
    for row in records:
        trace = run / 'runs' / Path(row['run_directory']).name / 'trace_legacy.json'
        check = dict(order=row['order'], arm=row['arm'], trace_present=trace.exists(),
                     prompt_matches=None, observed_models=[])
        if trace.exists():
            entries = json.loads(trace.read_text(encoding='utf-8'))['entries']
            expected_prompt = (ROOT / 'candidates' / row['arm'] / 'submission/prompts/system.md').read_text(encoding='utf-8')
            prompts = [e.get('content', '') for e in entries if e['type'] == 'system_instruction']
            check['prompt_matches'] = expected_prompt in prompts
            check['observed_models'] = sorted({e['model'] for e in entries if e.get('model')})
            check['required_model_only'] = bool(check['observed_models']) and all(
                'gemma-4-31b-it-qat-w4a16-ct' in m and m.endswith('/2') for m in check['observed_models'])
        treatments.append(check)
    archive = run.with_suffix('.zip')
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None:
            raise ValueError('Evidence ZIP CRC failure')
        for name in ('comparison_records.json', 'comparison_summary.json', 'comparison_status.json', 'registered_plan.json'):
            if z.read(name) != (run / name).read_bytes():
                raise ValueError(f'Download differs from original evidence ZIP: {name}')
    for arm in ('v0', 'v1'):
        rows = [r for r in records if r['arm'] == arm]
        tokens = [r['prompt_tokens'] + r['completion_tokens'] for r in rows if 'prompt_tokens' in r and 'completion_tokens' in r]
        summary['arms'][arm]['mean_observed_total_tokens'] = mean(tokens) if tokens else None
        summary['arms'][arm]['token_observed_runs'] = len(tokens)
    report = dict(run_id=run.name, status=json.loads(summaries[0].read_text()), summary=summary,
        kernel='wudangdexiaodoashi/gemma4-v1-paired-pilot', kernel_version=1,
        local_original_evidence_directory=str(run.resolve()),
        evidence_zip_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
        plan_sha256=hashlib.sha256((run / 'registered_plan.json').read_bytes()).hexdigest(),
        original_v0_files_unchanged=verify_frozen(), competition_score=None)
    report['treatment_checks'] = treatments
    report['treatment_integrity_confirmed'] = bool(treatments) and all(
        c.get('prompt_matches') is True and c.get('required_model_only') is True for c in treatments)
    target = ROOT / 'experiments/results/pilot-01'
    write_new(target / 'raw_comparison_records.json', (run / 'comparison_records.json').read_bytes())
    write_new(target / 'result_audit.json', (json.dumps(report, indent=2) + '\n').encode())
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('directory', type=Path)
    args = p.parse_args()
    print(json.dumps(collect(args.directory), indent=2))
