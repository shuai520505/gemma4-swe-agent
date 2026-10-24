"""Offline artifact/factor/tamper regressions against actual accepted bytes."""
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from .build import HERE,EGR,EXPECTED,sha,build,frozen_write
from .audit import inspect_archive


class ReleaseTests(unittest.TestCase):
    def test_factor_and_reproducible_frozen_artifacts(self):
        names=['submission_A.zip','submission_B.zip','submission_C.zip','CANDIDATE_MANIFEST.json']
        before={n:(HERE/n).read_bytes() for n in names}
        build()
        self.assertEqual(before,{n:(HERE/n).read_bytes() for n in names})
        self.assertEqual(before['submission_A.zip'],EGR.read_bytes())
        self.assertEqual(sha(before['submission_A.zip']),EXPECTED)
        with zipfile.ZipFile(io.BytesIO(before['submission_B.zip'])) as b,zipfile.ZipFile(io.BytesIO(before['submission_C.zip'])) as c:
            self.assertIsNone(b.testzip());self.assertIsNone(c.testzip())
            self.assertEqual(set(b.namelist()),set(c.namelist()))
            changed=[n for n in b.namelist() if b.read(n)!=c.read(n)]
            self.assertEqual(changed,['skills/meer-evidence/scripts/verify.py'])

    def test_immutable_writer_refuses_changed_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'artifact';frozen_write(p,b'ORIGINAL')
            with self.assertRaises(AssertionError):frozen_write(p,b'REPLACEMENT')
            self.assertEqual(p.read_bytes(),b'ORIGINAL')

    def test_repacked_source_tampering_is_rejected(self):
        proof=json.loads((HERE/'CPU_ACCEPTANCE_CPU03.json').read_bytes())
        raw=Path(proof['raw_archive_path']).read_bytes()
        self.assertEqual(sha(raw),proof['archive_sha256'])
        self.assertEqual(inspect_archive('cpu03',raw,require_bypass=True)['status'],'MEER_CPU_ENGINEERING_PASS')
        out=io.BytesIO()
        target='source/meer/v01/candidates/B/skills/meer-evidence/scripts/verify.py'
        with zipfile.ZipFile(io.BytesIO(raw)) as source,zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as altered:
            for name in source.namelist():
                content=source.read(name)
                if name==target:content=b'print("FAKE_PASS")\n'
                altered.writestr(name,content)
        # CRC is valid, but the actual source identity must still reject it.
        with zipfile.ZipFile(io.BytesIO(out.getvalue())) as z:self.assertIsNone(z.testzip())
        with self.assertRaises(AssertionError):inspect_archive('cpu03',out.getvalue(),require_bypass=True)


if __name__=='__main__':unittest.main(verbosity=2)
