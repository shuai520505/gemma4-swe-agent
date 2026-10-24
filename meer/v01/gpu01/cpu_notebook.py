"""Targeted CPU-only validation using the accepted once-only controller."""
import inspect
import json
import sys
import zipfile
import io
from .prepare import HERE, ROOT, PR30, MEER, sha


def build(attempt):
    from meer.v01 import notebook as original
    code = inspect.getsource(original.build)
    start = code.index('    source=ROOT/')
    end = code.index('    old=json.loads', start)
    replacement = '''    source=PR30
    with zipfile.ZipFile(HERE/'payload.zip') as z:
        files={n:z.read(n) for n in z.namelist() if n!='gpu_registration.json'}
    for name in ('cpu_acceptance.py','owned_transport.py'):
        files['meer/v01/'+name]=(MEER/name).read_bytes()
    files['meer/v01/gpu01/cpu_validation.py']=(HERE/'cpu_validation.py').read_bytes()
'''
    code = code[:start]+replacement+code[end:]
    code = code.replace('meer.v01.cpu_acceptance', 'meer.v01.gpu01.cpu_validation')
    code = code.replace('Agent_runs=4', 'Agent_runs=3')
    code = code.replace("sha((HERE/'CANDIDATE_MANIFEST.json').read_bytes())", "sha((MEER/'CANDIDATE_MANIFEST.json').read_bytes())")
    ns = dict(original.__dict__, HERE=HERE, ROOT=ROOT, MEER=MEER, PR30=PR30,
              ID='MEER-GPU-BINDING-CPU')
    exec(compile(code,'<Reused-sealed-CPU-builder>','exec'),ns)
    ns['build'](attempt)


def validate(attempt):
    b = json.loads((HERE/attempt/'BUILD.json').read_bytes())
    raw = (HERE/attempt/'payload.zip').read_bytes()
    assert sha(raw)==b['payload_sha256']
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        assert z.testzip() is None
        for n,h in b['payload_members'].items():
            assert sha(z.read(n))==h
        shared = json.loads((HERE/'PAYLOAD_BUILD.json').read_bytes())
        for n,h in shared['payload_members'].items():
            assert sha(z.read(n))==h
    assert sha((HERE/attempt/'notebook/study.ipynb').read_bytes())==b['Notebook_sha256']


def factory(attempt):
    from meer.v01 import notebook as original
    source=inspect.getsource(original.factory)
    source=source.replace('agent_runs==4','agent_runs==3').replace('agent_runs=4','agent_runs=3')
    ns=dict(original.__dict__,HERE=HERE,ROOT=ROOT,ID='MEER-GPU-BINDING-CPU',validate=validate)
    exec(compile(source,'<Accepted-once-only-CPU-controller>','exec'),ns)
    return ns['factory'](attempt)


if __name__=='__main__':
    command,attempt=sys.argv[1:3]
    if command=='build':build(attempt)
    elif command=='launch':factory(attempt).launch()
    elif command=='collect':factory(attempt).collect(sys.argv[3])
