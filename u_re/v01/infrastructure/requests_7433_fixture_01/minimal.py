"""Synthetic fixture-resolution study, never injected into Requests or an Agent.

The providers return labelled sentinel strings, not an HTTP implementation.
This isolates pytest's name-resolution rules and cannot repair Requests tests.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET


def counts(path):
    root = ET.parse(path).getroot()
    cases = list(root.iter('testcase'))
    return dict(tests=len(cases), failures=sum(c.find('failure') is not None for c in cases),
                errors=sum(c.find('error') is not None for c in cases),
                skipped=sum(c.find('skipped') is not None for c in cases))


def run(output):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    project = output/'toy_project'
    project.mkdir()
    (project/'conftest.py').write_text('''import pytest
@pytest.fixture
def httpbin(httpbin):
    return "wrapped:" + httpbin
@pytest.fixture
def httpbin_secure(httpbin_secure):
    return "wrapped:" + httpbin_secure
''')
    (project/'test_wrapper.py').write_text('''def test_plain(httpbin):
    assert httpbin == "wrapped:SYNTHETIC-PLAIN"
def test_secure(httpbin_secure):
    assert httpbin_secure == "wrapped:SYNTHETIC-SECURE"
''')
    plugins = output/'toy_plugins'
    plugins.mkdir()
    (plugins/'toy_provider.py').write_text('''import pytest
@pytest.fixture
def httpbin():
    return "SYNTHETIC-PLAIN"
@pytest.fixture
def httpbin_secure():
    return "SYNTHETIC-SECURE"
''')
    info = plugins/'ure_fixture_study_only-0.0.dist-info'
    info.mkdir()
    (info/'METADATA').write_text('Metadata-Version: 2.1\nName: ure-fixture-study-only\nVersion: 0.0\n')
    (info/'entry_points.txt').write_text('[pytest11]\nure_fixture_study_only = toy_provider\n')
    rows = []
    cases = [('missing_provider', False, True, False, 1, 2),
             ('explicit_provider', True, True, True, 0, 0),
             ('autoload_provider', True, False, False, 0, 0),
             ('autoload_disabled', True, True, False, 1, 2)]
    for name, expose, disable, explicit, expected_exit, expected_errors in cases:
        folder = output/name
        folder.mkdir()
        env = os.environ.copy()
        env.pop('PYTEST_ADDOPTS', None)
        env.pop('PYTEST_PLUGINS', None)
        env.pop('PYTEST_DISABLE_PLUGIN_AUTOLOAD', None)
        env.pop('PYTHONPATH', None)
        if expose:
            env['PYTHONPATH'] = str(plugins)
        if disable:
            env['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = '1'
        command = [sys.executable, '-m', 'pytest', str(project/'test_wrapper.py'), '-q',
                   '--confcutdir='+str(project), '--junitxml='+str(folder/'junit.xml')]
        if explicit:
            command += ['-p', 'toy_provider']
        result = subprocess.run(command, cwd=project, env=env, capture_output=True, text=True, timeout=60)
        (folder/'stdout.txt').write_text(result.stdout)
        (folder/'stderr.txt').write_text(result.stderr)
        row = dict(name=name, command=command, python=sys.version, pytest=__import__('pytest').__version__,
                   environment={n:env.get(n) for n in ('PYTHONPATH','PYTEST_DISABLE_PLUGIN_AUTOLOAD','PYTEST_PLUGINS','PYTEST_ADDOPTS')},
                   exit_code=result.returncode, counts=counts(folder/'junit.xml'),
                   scope='Synthetic name-resolution only; not a Requests provider or environment repair')
        row['expected_observed'] = (row['exit_code']==expected_exit and row['counts']['errors']==expected_errors
                                    and row['counts']['failures']==0 and row['counts']['tests']==2)
        (folder/'result.json').write_text(json.dumps(row, indent=2)+'\n')
        rows.append(row)
    summary = dict(passed=all(r['expected_observed'] for r in rows), cases=rows,
                   official_workspace_used=False, production_patch=False)
    (output/'result.json').write_text(json.dumps(summary, indent=2)+'\n')
    return summary


if __name__ == '__main__':
    result=run(sys.argv[1])
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['passed'] else 1)
