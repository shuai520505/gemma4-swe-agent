import hashlib
import json
from pathlib import Path, PurePosixPath
import unittest
import zipfile
from u_re.v01.build import HERE, archive


class PackageTests(unittest.TestCase):
    def test_two_packages_only_expected_factor(self):
        manifest=json.loads((HERE/'CANDIDATES.json').read_text())
        members={}
        for arm in ('noegv','full'):
            raw=(HERE/f'submission_{arm}.zip').read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(),manifest['candidates'][arm]['zip_sha256'])
            with zipfile.ZipFile(HERE/f'submission_{arm}.zip') as z:
                self.assertIsNone(z.testzip());self.assertEqual(len(z.namelist()),3)
                self.assertEqual(set(z.namelist()),{'agent.yaml','eval_config.yaml','prompts/system.md'})
                members[arm]={n:z.read(n) for n in z.namelist()}
                for name,data in members[arm].items():
                    self.assertEqual(data,(HERE/f'candidate_{arm}'/name).read_bytes())
                    self.assertFalse(PurePosixPath(name).is_absolute());self.assertNotIn('..',PurePosixPath(name).parts)
                self.assertEqual(raw,archive(members[arm]))
        self.assertEqual([n for n in members['full'] if members['full'][n]!=members['noegv'][n]],['prompts/system.md'])
        block=(HERE/'prompts/egv.md').read_text().strip()+'\n\n'
        self.assertEqual(members['full']['prompts/system.md'].decode().replace(block,'',1),members['noegv']['prompts/system.md'].decode())

    def test_single_agent_six_tools_no_interpolation(self):
        for arm in ('noegv','full'):
            y=(HERE/f'candidate_{arm}/agent.yaml').read_text()
            self.assertEqual(y.count('agent_class: LlmAgent'),1)
            for bad in ('agent_tool','sub_agents','Jev','callbacks','!ENV'):
                self.assertNotIn(bad,y)
            self.assertEqual([s.strip()[2:] for s in y.splitlines() if s.strip().startswith('- ')],
                ['get_status','run_command','read_file','edit_file','write_file','submit_patch'])
            prompt=(HERE/f'candidate_{arm}/prompts/system.md').read_text()
            self.assertNotIn('{',prompt);self.assertNotIn('}',prompt)
            self.assertIn('Run relevant ordinary tests',prompt)
            self.assertIn('After a successful submit_patch',prompt)
            self.assertIn('NO_INCREMENTAL_PROGRESS',prompt)
        self.assertNotIn('Evidence-gated verification:',(HERE/'candidate_noegv/prompts/system.md').read_text())
        self.assertIn('Evidence-gated verification:',(HERE/'candidate_full/prompts/system.md').read_text())

    def test_prompt_size_is_bounded(self):
        for arm in ('noegv','full'):
            self.assertLessEqual(len((HERE/f'candidate_{arm}/prompts/system.md').read_text().split()),650)


if __name__=='__main__':
    unittest.main()
