"""Read-only integrity checks for the research delivery; no model calls."""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from harness_v2.integrity import verify_baseline


def main():
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    manifest = json.loads((HERE / 'evidence-manifest.json').read_text())
    for name, digest in manifest['files'].items():
        assert sha(HERE / name) == digest, name
    baseline_count = verify_baseline(ROOT)
    registered = json.loads((ROOT / 'harness_v2/registrations/r12.json').read_text())
    for name, digest in registered['source_hashes'].items():
        assert sha(ROOT / name) == digest, name
    protected = ['candidates', 'harness_v2', 'experiments', 'docs/validation', 'scripts/official_wheels.json']
    changes = subprocess.check_output(['git', 'diff', '--name-only', manifest['origin_commit'], '--', *protected], cwd=ROOT, text=True)
    assert not changes.strip(), changes
    documents = ['RESEARCH_REVIEW.md', 'PUBLIC_SOLUTIONS.md', 'LORA_DATA_PLAN.md', 'NEXT_EXPERIMENTS.md']
    local_links = 0
    for name in documents:
        text = (ROOT / name).read_text(encoding='utf-8')
        assert '\ufffd' not in text, name
        for target in re.findall(r'\]\(([^)]+)\)', text):
            if '://' in target or target.startswith('#'):
                continue
            assert (ROOT / target.split('#')[0]).exists(), (name, target)
            local_links += 1
    comparison = json.loads((HERE / 'wheelhouse-comparison.json').read_text())
    public = json.loads((HERE / 'v19-static-audit.json').read_text())
    assert comparison['all_7_equal_s0'] and comparison['downloaded_sources_checked'] == 57
    assert public['crc_ok'] and public['notebook_export_byte_identical'] and len(public['members']) == 11
    print(json.dumps({'kind': 'integrity_and_research_checks_not_gemma_repair', 'frozen_baseline_files': baseline_count, 'r12_source_hashes': len(registered['source_hashes']), 'protected_tracked_diff_empty': True, 'research_evidence_hashes': len(manifest['files']), 'local_document_links': local_links, 'current_wheels_equal_s0': 7, 'cpu_source_hashes_verified': 57, 'v19_members_verified': 11, 'training_started': False, 'gpu_repair_experiment_run': False}, indent=2))


if __name__ == '__main__':
    main()
