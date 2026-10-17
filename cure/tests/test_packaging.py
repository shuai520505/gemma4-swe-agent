import hashlib
import json
from pathlib import Path
import unittest
import zipfile
from cure.build import AGENT_FILES

ROOT = Path(__file__).resolve().parents[2]


class PackagingTests(unittest.TestCase):
    def test_archives_contain_only_four_reviewed_files(self):
        for arm in ('checklist', 'cure_v01'):
            src = ROOT / 'cure/candidates' / arm
            self.assertEqual({p.relative_to(src).as_posix() for p in src.rglob('*') if p.is_file()}, set(AGENT_FILES))
            with zipfile.ZipFile(ROOT / 'cure/packages' / arm / 'submission.zip') as z:
                self.assertIsNone(z.testzip())
                self.assertEqual(set(z.namelist()), set(AGENT_FILES))
                for n in AGENT_FILES: self.assertEqual(z.read(n), (src / n).read_bytes())
        for shared in ('sampling.yaml', 'eval_config.yaml'):
            self.assertEqual((ROOT / 'cure/candidates/checklist' / shared).read_bytes(), (ROOT / 'cure/candidates/cure_v01' / shared).read_bytes())

    def test_templates_are_versioned_and_cpu_only(self):
        template = ROOT / 'cure/notebooks/cpu-metadata-template.json'
        meta = json.loads(template.read_text())
        self.assertIs(meta['enable_gpu'], False)
        self.assertFalse(meta['model_sources'])
        compile((template.parent / 'install_official.py').read_text(), '<install-cell>', 'exec')
