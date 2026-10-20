"""Reuse the frozen real official-tool fixture in memory, never edit it on disk.

Scripted HTTP tests execution capability, not autonomous prompt compliance.
"""
from pathlib import Path
from unittest.mock import patch
from s2.egv_agenttool_t500_v01.tests import runner_cases as prior

HERE=Path(__file__).resolve().parent
ORIGINAL_PLAN=prior.plan
call,edit=prior.call,prior.edit
BAD,FIRST,GOOD=prior.BAD,prior.FIRST,prior.GOOD
EARLY_REQUEST=('Pre-repair verification: production app.py is unchanged. Issue requires accepts(0)=True and accepts(-1)=False. '
    'Located app.py; hypothesis: inclusive boundary is required. Falsify the current implementation with python3 checks.py, '
    'confirm its workspace path, check negative behavior and return evidence. No patch exists. Shared budget is500s/60tools; get_status first.')
FAIL=('Verification status: FAIL\nCounterevidence: zero is rejected by current workspace app.py. '
    'Execution evidence: python3 checks.py failed TARGET_BOUNDARY. Negative case remains unverified. '
    'Recommended next action: repair the inclusive boundary and retest.')
PASS='Verification status: PASS for checks.py only; target and old-negative assertions passed. No complete-task claim.'


def plan(case):
    if case in ('early_only','early_repair'):
        main=[call('get_status'),call('read_file',filepath='app.py'),call('egv_verifier',request=EARLY_REQUEST)]
        child=[call('get_status'),call('read_file',filepath='app.py'),call('run_command',command='python3 checks.py'),FAIL]
        if case=='early_only':main+=['FAIL received; no patch yet; accurately unverified.']
        else:main += [edit(BAD,GOOD),call('run_command',command='python3 checks.py'),
            call('run_command',command='git diff --check && git diff'),call('submit_patch'),'Complete with executed evidence.']
        return main,child
    if case=='cleanup':
        return ([call('write_file',filepath='scratch_probe.py',content="print('temporary diagnostic')\n"),
            edit(BAD,GOOD),call('run_command',command='python3 checks.py'),
            call('run_command',command='rm scratch_probe.py && git diff --check && git diff'),
            call('submit_patch'),'Complete; only intended source change submitted.'],[])
    if case in ('wrong_expectation','production_regression','probe_environment','unverified'):
        probe={
            'wrong_expectation':"python3 -c \"import app; assert app.accepts(0) is False, 'WRONG_EXPECTATION'\"",
            'production_regression':"python3 -c \"import app; assert app.accepts(0) is True, 'TARGET_BOUNDARY'\"",
            'probe_environment':"python3 -c \"import deliberately_absent_probe_dependency\"",
            'unverified':"python3 -c \"print('import or exit zero is not behavior validation')\""}[case]
        main=[edit(BAD,FIRST if case=='production_regression' else GOOD),call('run_command',command=probe)]
        if case!='unverified':main+=[call('run_command',command='python3 checks.py')]
        main+=['Probe outcome recorded; no self-certified PASS.']
        return main,[]
    return ORIGINAL_PLAN(case)


async def exercise(case,directory,**kwargs):
    with patch.object(prior,'HERE',HERE),patch.object(prior,'plan',plan):
        return await prior.exercise(case,directory,**kwargs)
