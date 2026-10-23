"""Read/reconcile existing GPU03 only;offline metrics never affect Agent decisions."""
import json,types
from pathlib import Path
from .notebook import HERE,ROOT,SLUG,sha

def collect(private_root):
    path=HERE.parent/'real_gemma_abba01/collect.py';source=path.read_text(encoding='utf-8')
    source=source.replace('from .GPU_NOTEBOOK import HERE,ROOT,SLUG','')
    source=source.replace('u_re_actionfirst_abba01.zip','u_re_actionfirst_abba03.zip')
    m=types.ModuleType('gpu03_existing_read');m.__file__=str(path);exec(compile(source,str(path),'exec'),m.__dict__)
    m.HERE=HERE;m.ROOT=ROOT;m.SLUG=SLUG;m.collect(private_root)

def analyze(archive):
    receipt=json.loads((HERE/'execution/HTTP_RECEIPT.json').read_bytes())
    observations=sorted((HERE/'read_observations').glob('read-*/OUTPUT_MANIFEST.json'))
    assert observations
    manifest=json.loads(observations[-1].read_bytes());items=[f for f in manifest['files'] if f['file']=='u_re_actionfirst_abba03.zip']
    assert len(items)==1 and items[0]['Notebook_id']==receipt['Notebook_id'] and items[0]['version']==1
    archive=Path(archive);assert sha(archive.read_bytes())==items[0]['sha256']
    path=HERE.parent/'real_gemma_abba01/analyze.py';source=path.read_text(encoding='utf-8').replace('from .GPU_NOTEBOOK import HERE,ROOT','')
    source=source.replace('Notebook_id=140228050','Notebook_id='+str(receipt['Notebook_id']))
    for before,after in [('REAL_GEMMA_ABBA_COMPLETE','GPU03_REAL_GEMMA_ABBA_COMPLETE'),('REAL_GEMMA_ABBA_PARTIAL','GPU03_REAL_GEMMA_ABBA_PARTIAL'),('GPU_BLOCKED_BY_','GPU03_BLOCKED_BY_')]:source=source.replace(before,after)
    m=types.ModuleType('gpu03_existing_offline');m.__file__=str(path);exec(compile(source,str(path),'exec'),m.__dict__)
    m.HERE=HERE;m.ROOT=ROOT;m.analyze(archive)

if __name__=='__main__':
    import sys
    if sys.argv[1]=='collect':collect(sys.argv[2])
    elif sys.argv[1]=='analyze':analyze(sys.argv[2])
