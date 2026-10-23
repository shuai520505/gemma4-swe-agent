"""Research-only reader for pytest snapshot call+teardown duplicate records.

Never changes JUnit, pytest, assertions or the official native resolved verdict.
Unknown discrepancies remain STOP. The original research reader is unchanged.
"""
import json,xml.etree.ElementTree as ET
from pathlib import Path
from .dependencies import sha

MESSAGE='some snapshots in this test have incorrect values.'

def parse_snapshot_phases(raw):
    assert len(raw)<16*1024*1024
    root=ET.fromstring(raw);suites=[root] if root.tag=='testsuite' else list(root.findall('testsuite'))
    assert suites
    cases=[];events=[];redundant=0
    counts=dict(tests=0,failures=0,errors=0,skipped=0)
    for suite in suites:
        rows=list(suite.findall('testcase'));groups={}
        for case in rows:groups.setdefault((case.get('classname',''),case.get('name','')),[]).append(case)
        failures=[c for c in rows if c.find('failure') is not None]
        errors=[c for c in rows if c.find('error') is not None]
        skipped=[c for c in rows if c.find('skipped') is not None]
        assert int(suite.get('tests'))==len(groups)
        assert int(suite.get('failures'))==len(failures) and int(suite.get('errors'))==len(errors) and int(suite.get('skipped'))==len(skipped)
        assert errors and len(rows)==len(groups)+len(errors)
        for key,group in groups.items():
            assert len(group) in (1,2)
            if len(group)==2:
                calls=[c.find('failure') for c in group if c.find('failure') is not None]
                finalizers=[c.find('error') for c in group if c.find('error') is not None]
                assert len(calls)==len(finalizers)==1
                call,finalizer=calls[0],finalizers[0]
                assert 'snapshot(' in (call.text or '')
                assert call.get('message','').startswith(('AssertionError:','assert '))
                assert (finalizer.text or '').strip()==MESSAGE
                assert finalizer.get('message','')=='failed on teardown with "Failed: '+MESSAGE+'"'
                redundant+=1
            elif group[0].find('error') is not None:raise AssertionError('Unpaired independent error')
        for case in rows:
            for tag in ('failure','error'):
                node=case.find(tag)
                if node is not None:events.append(dict(classname=case.get('classname',''),name=case.get('name',''),message=node.get('message',''),details=node.text or '',category='assertion_failure' if tag=='failure' else 'snapshot_assertion_teardown'))
        counts['tests']+=len(groups);counts['failures']+=len(failures);counts['errors']+=len(errors);counts['skipped']+=len(skipped);cases+=rows
    assert redundant==counts['errors'] and redundant>0 and counts['failures']>=redundant
    return dict(category='assertion_failure',categories=['assertion_failure','snapshot_assertion_teardown'],counts=counts,summary=dict(passed=counts['tests']-counts['failures']-counts['skipped'],failed=counts['failures'],error=counts['errors'],skipped=counts['skipped']),events=events,infrastructure_stop=False,confirmed_failure=True,attribution='native_target_snapshot_assertion',reason='Exact paired snapshot call failures and duplicate teardown records; native negative verdict unchanged',snapshot_assertion_teardown_proven=True,duplicate_snapshot_finalizer_errors=redundant,JUnit_records=len(cases),environment_errors=0)

def audit_verifier(directory,**kwargs):
    from s1.verifier_v3.audit import audit_verifier as legacy
    result=legacy(directory,**kwargs)
    if result.get('category')!='unknown_unparsed' or 'JUnit aggregate mismatch:tests' not in result.get('reason',''):return result
    directory=Path(directory)
    try:
        raw=(directory/'phase2.junit.xml').read_bytes();capture=json.loads((directory/'phase2_junit_capture.json').read_bytes())
        assert capture['status']=='captured' and capture['sandbox_exists_at_capture'] and sha(raw)==capture['sha256']
        import importlib.metadata as md,inline_snapshot.pytest_plugin as plugin
        assert md.version('inline-snapshot')=='0.21.1'
        installed=sha(Path(plugin.__file__).read_bytes())
        manifest=json.loads((Path(__file__).parent/'NEW_DEPENDENCIES.json').read_bytes())
        wheel=next(r for r in manifest['packages'] if r['name']=='inline-snapshot')
        import zipfile
        with zipfile.ZipFile(Path(__file__).parent/'wheels'/wheel['filename']) as z:assert installed==sha(z.read('inline_snapshot/pytest_plugin.py'))
        new=parse_snapshot_phases(raw)
        assert json.loads((directory/'phase2_execution.json').read_bytes())['exit_code']==1
        new.update(exit_code=1,legacy_reader_reason=result['reason'],reader_scope='New research parser only; original JUnit and official Verifier bytes/result unchanged',plugin_source_sha256=installed)
        return new
    except Exception as exc:
        return dict(result,new_reader_failure=type(exc).__name__)
