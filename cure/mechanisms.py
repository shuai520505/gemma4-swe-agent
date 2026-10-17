"""Real CPU commands with scripted evidence decoders and edits; no Gemma involved."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from .action_selector import Budget, Checklist, select
from .contract_state import ContractBook, ContractState, Evidence
from .decision_log import DecisionLog
from .fixtures import CASES
from harness_v2.evidence import atomic_json


def command(workspace, code):
    start = time.monotonic()
    p = subprocess.run([sys.executable, '-B', '-c', code], cwd=workspace, capture_output=True, text=True, timeout=10)
    return p.returncode, p.stdout + p.stderr, time.monotonic() - start


def run_case(case, arm, directory, *, tool_limit=12, bad_edit=False):
    fixture = CASES[case]
    directory = Path(directory); directory.mkdir(parents=True, exist_ok=False)
    journal = DecisionLog(directory)
    book = ContractBook([ContractState('r1', fixture['requirement'], proposed_probe='Run the provided caller reproduction')])
    contract = book.contracts[0]
    contract.update(Evidence('unconfirmed_hypothesis', 'Initial implementation alone may satisfy the contract', 'initial-scripted-hypothesis'))
    checklist = Checklist(); actions = []; total = 0.; remaining = tool_limit; verified = False
    with tempfile.TemporaryDirectory(prefix='cure_mechanism_') as temp:
        workspace = Path(temp)
        for name, contents in [('app.py', fixture['source']), ('caller.py', fixture['caller']), ('probe.py', fixture['probe']), ('verify.py', fixture['verify'])]:
            (workspace / name).write_text(contents, encoding='utf-8')
        for args in (['git', 'init', '-q'], ['git', 'add', '.'], ['git', '-c', 'user.name=CureFixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'fixture']):
            subprocess.run(args, cwd=workspace, check=True, capture_output=True)
        for step in range(16):
            budget = Budget(max(0, 300 - total), remaining)
            decision = select(book, budget) if arm == 'C' else checklist.choose(book, budget)
            sequence = journal.begin(book, budget, decision)
            if not decision.feasible:
                journal.finish(sequence, {'status': 'budget_exhausted'}, decision.action, decision, 0, 0)
                break
            action = decision.action; actions.append(action)
            if action == 'locate': code = "from pathlib import Path; print(sorted(p.name for p in Path('.').glob('*.py')))"
            elif action == 'inspect':
                target = 'caller.py' if contract.contradiction_count else 'app.py'
                code = f"from pathlib import Path; print(Path({target!r}).read_text())"
            elif action in ('probe', 'verify'): code = f"exec(compile(open('{action}.py').read(), '{action}.py', 'exec')); print('CHECK_PASSED')"
            elif action == 'edit':
                replacement = fixture['replacement']
                if bad_edit and case == 'old_behavior': replacement = "def parse(value):\n    return None if not value else int(value)\n"
                code = f"from pathlib import Path; p=Path('app.py'); p.write_text({replacement!r}); compile(p.read_text(), 'app.py', 'exec'); print('SCRIPTED_EDIT_APPLIED')"
            else: code = "import subprocess; subprocess.run(['git','diff','--check'],check=True); print(subprocess.check_output(['git','diff'],text=True))"
            exit_code, output, elapsed = command(workspace, code)
            remaining -= 1; total += elapsed
            raw = {'exit_code': exit_code, 'output': output}
            (directory / f'{sequence:02d}-{action}.json').write_text(json.dumps(raw, indent=2), encoding='utf-8')
            same_budget = Budget(max(0, 300 - total), remaining)
            next_without = select(book, same_budget).action if arm == 'C' else checklist.choose(book, same_budget).action
            evidence = Evidence.tool_result(output, f'{sequence:02d}-{action}.json',
                role='verification' if action == 'verify' else ('edit' if action == 'edit' else ('probe' if action == 'probe' else 'read')), exit_code=exit_code)
            if action == 'locate' and exit_code == 0:
                contract.update(evidence, located=True, uncertainty=.7)
            elif action == 'inspect' and exit_code == 0:
                revisited = contract.contradiction_count > 0
                contract.update(evidence, inspected=True, ready_to_edit=revisited, uncertainty=.2 if revisited else .65)
            elif action == 'probe':
                # Explicit scenario decoder, not a general parser or learned diagnosis.
                overturns = fixture['contradiction'] and exit_code != 0
                contract.update(evidence, contradiction=overturns, uncertainty=.2 if not overturns else .95,
                                ready_to_edit=not overturns)
            elif action == 'edit' and exit_code == 0:
                contract.update(evidence, edited=True, verification_status='unverified')
                book.patch_ready = bool(subprocess.check_output(['git', 'diff'], cwd=workspace))
            elif action == 'verify':
                verified = exit_code == 0
                contract.update(evidence, verification_status='passed' if verified else 'failed',
                    contradiction=not verified, edited=verified)
            elif action == 'submit':
                contract.update(evidence)
                (directory / 'submitted.patch').write_text(output, encoding='utf-8')
            else:
                contract.update(evidence)
            checklist.advance()
            next_with = select(book, same_budget) if arm == 'C' else checklist.choose(book, same_budget)
            journal.finish(sequence, {'exit_code': exit_code, 'reference': evidence.reference, 'sha256': evidence.digest,
                'decoder': 'explicit_fixture_rules', 'edited_by': 'same_scripted_actor_for_both_arms'},
                next_without, next_with, elapsed, 1)
            if action == 'submit': break
        result = dict(case=case, arm=arm, actions=actions, tools_used=tool_limit - remaining,
            duration_seconds=total, patch_ready=book.patch_ready, verification_passed=verified,
            contradictions=contract.contradiction_count, final_state=book.snapshot(),
            kind='scripted_CPU_mechanism_not_Gemma_or_Kaggle', bad_edit=bad_edit)
    atomic_json(directory / 'result.json', result)
    return result


def run_suite(output):
    output = Path(output); output.mkdir(parents=True, exist_ok=False)
    records = []
    for case in CASES:
        for arm in ('B', 'C'):
            records.append(run_case(case, arm, output / f'{case}-{arm}'))
    for arm in ('B', 'C'):
        records.append(run_case('interface', arm, output / f'tight-budget-{arm}', tool_limit=6))
        records.append(run_case('old_behavior', arm, output / f'regression-failure-{arm}', bad_edit=True))
    atomic_json(output / 'results.json', records)
    return records


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('output', type=Path)
    rows = run_suite(p.parse_args().output)
    print(json.dumps([{k: r[k] for k in ('case', 'arm', 'tools_used', 'duration_seconds', 'verification_passed', 'actions', 'bad_edit')} for r in rows], indent=2))
