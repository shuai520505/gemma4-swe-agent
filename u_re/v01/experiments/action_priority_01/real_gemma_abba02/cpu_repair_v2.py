"""Independent CPU-only version after preserved import-repair01 ERROR."""
from . import cpu_repair
from .notebook import HERE,ROOT

def files():
    result=cpu_repair.corrected_files()
    for name in ('runtime_worker.py','cpu_probe_v2.py'):
        p=HERE/name;result[p.relative_to(ROOT).as_posix()]=p.read_bytes()
    return result

def factory():
    return cpu_repair.factory(cpu=HERE/'repair_cpu02',execution_id='U-RE-ACTION-FIRST-GPU02-WORKER-REPAIR02',
        slug='wudangdexiaodoashi/gemma4-u-re-abba02-worker-repair02',probe_module='cpu_probe_v2',
        archive='u_re_abba02_worker_repair02',files_factory=files)

if __name__=='__main__':
    import sys
    m=factory()
    if sys.argv[1]=='build':m.build()
    elif sys.argv[1]=='launch':m.launch()
    elif sys.argv[1]=='collect':m.collect(sys.argv[2])
