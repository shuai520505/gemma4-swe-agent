import tempfile
import unittest
import zipfile
from pathlib import Path
from scripts.agent_config import ROOT, MODEL, TOOLS, MEMBERS, build, compile_adk, load, validate
import yaml


class SubmissionTests(unittest.TestCase):
    def fixture(self, root):
        target = root / 'submission'
        (target / 'prompts').mkdir(parents=True)
        for name in MEMBERS:
            (target / name).write_bytes((ROOT / 'submission' / name).read_bytes())
        return target

    def test_real_adk_loader(self):
        agent = compile_adk(ROOT / 'submission')
        self.assertEqual(agent.model.model, 'openai/' + MODEL)
        self.assertEqual([tool.__name__ for tool in agent.tools], TOOLS)
        self.assertEqual(agent.instruction, (ROOT / 'submission/prompts/system.md').read_text())

    def test_archive_layout_and_repeatability(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            a, b = root / 'a.zip', root / 'b.zip'
            self.assertEqual(build(ROOT / 'submission', a), build(ROOT / 'submission', b))
            with zipfile.ZipFile(a) as archive:
                self.assertEqual(archive.namelist(), MEMBERS)
                self.assertIsNone(archive.testzip())
                archive.extractall(root / 'extracted')
            validate(root / 'extracted')
            compile_adk(root / 'extracted')

    def test_model_and_prompt_tampering_rejected(self):
        for field, value in [('model', 'other-model'), ('instruction', 'mismatch'), ('sub_agents', [])]:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temp:
                target = self.fixture(Path(temp))
                config = load(target / 'agent.yaml')
                config[field] = value
                (target / 'agent.yaml').write_text(yaml.safe_dump(config))
                with self.assertRaises(ValueError):
                    validate(target)

    def test_unapproved_or_missing_tools_rejected(self):
        for tools in [[], ['google_search'], TOOLS[:-1]]:
            with self.subTest(tools=tools), tempfile.TemporaryDirectory() as temp:
                target = self.fixture(Path(temp))
                config = load(target / 'agent.yaml')
                config['tools'] = tools
                (target / 'agent.yaml').write_text(yaml.safe_dump(config))
                with self.assertRaises(ValueError):
                    validate(target)

    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = self.fixture(root)
            (target / 'prompts/system.md').unlink()
            (target / 'prompts/system.md').symlink_to(ROOT / 'submission/prompts/system.md')
            with self.assertRaises(ValueError):
                build(target, root / 'bad.zip')


if __name__ == '__main__':
    unittest.main()
