"""Official Linux CPU execution. No Gemma inference, no GPU authorization."""
import importlib
import importlib.metadata
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from harness_v2.evidence import atomic_json


def main(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    reg=json.loads(Path('s2/registration.json').read_text())
    wheelhouse=next(Path('/kaggle/input').rglob('swegemma-0.2.11-py3-none-any.whl')).parent
    import hashlib
    actual={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in wheelhouse.glob('*.whl')}
    atomic_json(output/'wheel_hashes.json',actual)
    assert actual==reg['wheel_hashes'],'Official wheelhouse drift; do not reinterpret prior evidence'
    source=output/'official_source';source.mkdir()
    modules=['adk_submission.schema','adk_submission.resolvers.tools','adk_submission.yaml_loader',
             'adk_submission.context','adk_submission.builders.llm','google.adk.tools.agent_tool',
             'google.adk.runners','swegemma.context','swegemma.tools.base','swegemma.tools.execution',
             'swegemma.harness.agent_runner']
    meta={}
    for name in modules:
        m=importlib.import_module(name);raw=Path(inspect.getfile(m)).read_bytes();target=name.replace('.','_')+'.py'
        (source/target).write_bytes(raw);meta[name]=dict(path=inspect.getfile(m),sha256=hashlib.sha256(raw).hexdigest())
    for f in Path('/kaggle/input').rglob('HARNESS_README.md'):
        raw=f.read_bytes();(source/'HARNESS_README.md').write_bytes(raw);meta['HARNESS_README']=dict(path=str(f),sha256=hashlib.sha256(raw).hexdigest());break
    atomic_json(output/'official_source_index.json',meta)
    versions={n:importlib.metadata.version(n) for n in ('swegemma','adk-submission','adk-eval-core','google-adk','google-genai','litellm','pytest')}
    atomic_json(output/'versions.json',versions)
    os.environ['S2_CPU_EVIDENCE']=str(output/'cases')
    suite=unittest.defaultTestLoader.loadTestsFromName('s2.egv_agenttool_v01.tests.test_closed_loop')
    with (output/'new_tests.log').open('x') as log:
        result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    gate=dict(passed=result.wasSuccessful() and not result.skipped,test_methods=result.testsRun,
        failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),
        real_Compiler=True,real_ADK_Runner=True,mocked_HTTP=True,Gemma_inference=False,GPU=False,versions=versions)
    atomic_json(output/'new_gate.json',gate)
    assert gate['passed'],'Inspect new actual Runner failures; preserve this preparation, version the fix'
    # Re-execute the accepted full old115 path in a separate process, without
    # editing those sources or substituting a prior successful test log.
    old=subprocess.run([sys.executable,'-m','s1.experiments.egv_mechanism_smoke_01.cpu',str(output/'original115')],capture_output=True,text=True,timeout=3000)
    (output/'original115.stdout.log').write_text(old.stdout);(output/'original115.stderr.log').write_text(old.stderr)
    prior=json.loads((output/'original115/cpu_gate.json').read_text())
    gate.update(original115=prior,passed=old.returncode==0 and prior['passed'],
                source_hashes=reg['source_hashes'],scope='New test methods contain separate named scenarios; do not count scenarios as independent GPU tasks.')
    atomic_json(output/'cpu_gate.json',gate)
    assert gate['passed']
    print(json.dumps({k:v for k,v in gate.items() if k not in ('source_hashes','original115')},indent=2))


if __name__=='__main__':main(sys.argv[1])
