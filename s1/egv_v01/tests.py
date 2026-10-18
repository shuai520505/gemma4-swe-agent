"""Official real Runner with mocked HTTP; no Gemma behavior inference."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from s1.tests import test_runner
from s1.util import sha_file

HERE=Path(__file__).resolve().parent


class CandidateTests(unittest.IsolatedAsyncioTestCase):
    async def test_actual_empty_state_runner_control_and_EGV(self):
        manifest=json.loads((HERE/'candidate.json').read_text())
        target=Path(os.environ['EGV_CPU_EVIDENCE'])/'runner'
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for arm,source in [('control',Path('s1/candidates/control')),('egv',HERE/'candidate')]:
                for file in source.rglob('*'):
                    if file.is_file():
                        dest=root/'candidates'/arm/file.relative_to(source)
                        dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(file.read_bytes())
            (root/'candidates.json').write_text(json.dumps({arm:dict(config=manifest['config']) for arm in ('control','egv')}))
            helper=test_runner.FullRunnerTests(methodName='runTest')
            with patch.object(test_runner,'ROOT',root),patch.dict(os.environ,S1_RUNNER_EVIDENCE=str(target)):
                await helper.exercise('control')
                await helper.exercise('egv')
        control=json.loads(next(target.glob('control*/result.json')).read_text())
        egv=json.loads(next(target.glob('egv*/result.json')).read_text())
        self.assertEqual(control['wire'][0]['tools'],egv['wire'][0]['tools'])
        for key in ('max_tokens','max_completion_tokens','thinking_token_budget','chat_template_kwargs','seed','temperature','top_p','top_k'):
            self.assertEqual(control['wire'][0].get(key),egv['wire'][0].get(key))
        prompt=(HERE/'candidate/prompts/system.md').read_text()
        self.assertIn(prompt.strip(),egv['rendered_system'])
        self.assertIn('S1 CPU Issue with JSON {"x": [1, 2]}.',str(egv['wire'][0]['messages']))
        (target/'compiled_and_rendered_instruction.txt').write_text(egv['rendered_system'])

    async def test_single_factor_package_and_official_compilation(self):
        from adk_submission import ModelRegistry,compile_submission,validate_directory
        from google.adk.models.lite_llm import LiteLlm
        from swegemma.context import SwegemmaContext
        from swegemma.config import build_submission_limits
        from s1 import MODEL
        from s1.config import Config,validate_compiled
        manifest=json.loads((HERE/'candidate.json').read_text())
        self.assertEqual(sha_file(HERE/'submission.zip'),manifest['zip_sha256'])
        with zipfile.ZipFile(HERE/'submission.zip') as z:
            self.assertEqual(set(z.namelist()),{'agent.yaml','eval_config.yaml','prompts/system.md'})
            for name in z.namelist():self.assertEqual(z.read(name),(HERE/'candidate'/name).read_bytes())
        for name in ('agent.yaml','eval_config.yaml'):
            self.assertEqual((HERE/'candidate'/name).read_bytes(),(Path('s1/candidates/control')/name).read_bytes())
        prompt=(HERE/'candidate/prompts/system.md').read_bytes()
        self.assertTrue(prompt.startswith(Path('s1/candidates/control/prompts/system.md').read_bytes()))
        self.assertLessEqual(len(manifest['added_rule'].split()),120)
        self.assertNotIn(b'{',manifest['added_rule'].encode())
        models=ModelRegistry();models.register(MODEL,LiteLlm(model='openai/'+MODEL,api_base='http://127.0.0.1:8000/v1',api_key='EMPTY'))
        limits,constraints=build_submission_limits();validate_directory(HERE/'candidate',limits=limits)
        agent=compile_submission(HERE/'candidate',SwegemmaContext().create_tools(),models,limits=limits,generation_constraints=constraints)
        validate_compiled(agent,Config(**manifest['config']))
        # The official include reader performs universal-newline text loading.
        # Preserve raw package bytes separately; normalize ONLY actual CRLF,
        # never JSON escape sequences,words,spaces or template markers.
        self.assertEqual(agent.instruction.strip(),prompt.decode().replace('\r\n','\n').strip())
        out=Path(os.environ['EGV_CPU_EVIDENCE']);(out/'compiled_instruction.txt').write_text(agent.instruction)
