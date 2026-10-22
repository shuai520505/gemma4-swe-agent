"""Reuse offline metrics parser;bind GPU02 identity/ZIP before reading results."""
import json
from pathlib import Path
import types
from .notebook import HERE,ROOT,ORIGINAL,sha

def analyze(archive):
    receipt=json.loads((HERE/'execution/HTTP_RECEIPT.json').read_bytes())
    observations=sorted((HERE/'read_observations').glob('read-*/OUTPUT_MANIFEST.json'))
    assert observations
    manifest=json.loads(observations[-1].read_bytes())
    matches=[f for f in manifest['files'] if f['file']=='u_re_actionfirst_abba02.zip']
    assert len(matches)==1 and matches[0]['Notebook_id']==receipt['Notebook_id'] and matches[0]['version']==1
    archive=Path(archive);assert sha(archive.read_bytes())==matches[0]['sha256']
    source=(ORIGINAL/'analyze.py').read_text(encoding='utf-8').replace('from .GPU_NOTEBOOK import HERE,ROOT','')
    source=source.replace('Notebook_id=140228050',"Notebook_id="+str(receipt['Notebook_id']))
    m=types.ModuleType('gpu02_existing_offline_metrics');m.__file__=str(ORIGINAL/'analyze.py')
    exec(compile(source,m.__file__,'exec'),m.__dict__);m.HERE=HERE;m.ROOT=ROOT;m.analyze(archive)

if __name__=='__main__':
    import sys
    analyze(sys.argv[1])
