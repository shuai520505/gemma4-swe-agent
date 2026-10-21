import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest
import zipfile

from u_re.v01.experiments.fastapi_pilot_01.register import HERE,PREVIOUS,ROOT
from u_re.v01.experiments.fastapi_pilot_01.screen import decide
from u_re.v01.experiments.fastapi_pilot_01.auth_diagnose import redact


class PolicyTests(unittest.TestCase):
    def test_rank_and_all_exclusions_are_byte_identical(self):
        for n in ('RANKED_POOL.json','EXCLUSION_LEDGER_V02.json','TASK_POOL_METADATA.json'):
            self.assertEqual((HERE/n).read_bytes(),(PREVIOUS/n).read_bytes())
        rows=json.loads((HERE/'RANKED_POOL.json').read_bytes())['rows']
        ids=json.loads((HERE/'EXCLUSION_AUDIT.json').read_bytes())['excluded_task_ids']
        self.assertEqual(len(ids),79);self.assertEqual(len(rows),50)
        self.assertFalse({r['instance_id'] for r in rows}&set(ids))
        self.assertEqual({r['repo'] for r in rows},{'fastapi/fastapi'})

    def test_only_expected_design_scope_changed(self):
        p=json.loads((HERE/'SELECTION_PROTOCOL.json').read_bytes())
        self.assertEqual(p['selection_algorithm']['max_cpu_checks'],8)
        self.assertEqual(p['future_order'],['A','B','B','A'])
        self.assertEqual(p['budget'],dict(agent_seconds=300,counted_tools=60,command_seconds=120))
        code=(HERE/'screen.py').read_text()
        self.assertNotIn('SKIPPED_REPOSITORY_ALREADY_SELECTED',code)
        self.assertIn("row['instance_id'] not in",code)
        ast.parse(code)

    def test_structured_assertions_eligible_but_success_or_unknown_not(self):
        self.assertEqual(decide(dict(category='assertion_failure',infrastructure_stop=False),evidence_ok=True)[0],'ELIGIBLE')
        self.assertEqual(decide(dict(category='passed',infrastructure_stop=False),evidence_ok=True)[0],'REJECT')
        self.assertEqual(decide(dict(category='unknown_unparsed',infrastructure_stop=True),evidence_ok=True)[0],'STOP')
        self.assertEqual(decide(dict(category='assertion_failure',infrastructure_stop=False),evidence_ok=False)[0],'STOP')

    def test_frozen_zip_and_member_pins(self):
        pins=json.loads((HERE/'SELECTION_PROTOCOL.json').read_bytes())['candidates']['candidates']
        for arm,pin in pins.items():
            path=ROOT/'u_re/v01'/('submission_'+arm+'.zip')
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),pin['zip_sha256'])
            with zipfile.ZipFile(path) as z:
                self.assertIsNone(z.testzip())
                self.assertEqual({n:hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist()},pin['members'])

    def test_gpu_guard_exits_before_external_work(self):
        tree=ast.parse((HERE/'gpu_execution_stub.py').read_text())
        self.assertEqual(len(tree.body),2);self.assertIsInstance(tree.body[1],ast.Raise)
        p=subprocess.run([sys.executable,str(HERE/'gpu_execution_stub.py')],capture_output=True,text=True)
        self.assertNotEqual(p.returncode,0);self.assertIn('NOT_AUTHORIZED',p.stderr)

    def test_diagnostic_redaction_removes_secrets_and_home_paths(self):
        fake='private-demo-value';text='Token='+fake+' '+str(Path.home())+' Bearer: example_secret'
        output=redact(text,[fake])
        self.assertNotIn(fake,output);self.assertNotIn(str(Path.home()),output)
        self.assertNotIn('example_secret',output)


if __name__=='__main__':unittest.main()
