"""Environment repair must preserve original bug/positive-control observations."""
from pathlib import Path
from unittest.mock import patch
from gemma_pair.data import prepare
from gemma_pair.sandbox import SubprocessManager
from gemma_pair.evaluate import evaluate

def run(out,repair):
    out=Path(out);out.mkdir(exist_ok=False)
    data=prepare(out/'data')
    class RepairedManager(SubprocessManager):
        def start(self):
            sid=super().start()
            repair(self.sandboxes[sid]['root'])
            return sid
    # This is a CPU test of the research adapter, not a competitor callback or
    # a change to the original six-session native tool/Agent configuration.
    RepairedManager.__name__='SubprocessManager'
    rows={}
    with patch('gemma_pair.evaluate.SubprocessManager',RepairedManager):
        for task,binding in data.items():
            result=evaluate(binding,out/task)
            assert result['target_failed'] and result['positive_controls_passed'] and result['cleanup']
            assert result['check_write_denied'] and result['check_unchanged'] and result['source_unchanged_by_checks']
            rows[task]={k:result[k] for k in ('target_failed','positive_controls_passed','cleanup','check_write_denied','check_unchanged','source_unchanged_by_checks')}
    return rows
