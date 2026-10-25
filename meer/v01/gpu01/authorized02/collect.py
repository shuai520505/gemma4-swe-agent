"""Existing accepted versions only; never save or restart a Notebook."""
import json,re,shutil,types
from pathlib import Path
from .read_preflight import HERE,GPU,PRIVATE,save

def collect(batch):
    directory=HERE/f'batch{batch:02d}'
    receipts=list(directory.glob('execution*/HTTP_RECEIPT.json'))
    assert len(receipts)==1,'Require one actual dispatch receipt'
    receipt=json.loads(receipts[0].read_bytes());assert receipt['accepted_version']==1
    results=list(directory.glob('CLI_PUSH_RESULT*.json'));assert len(results)==1
    result=json.loads(results[0].read_bytes())
    refs=re.findall(r'https://www\.kaggle\.com/code/([a-z0-9_-]+/[a-z0-9_-]+)',result['stdout'])
    assert len(refs)==1 and refs[0].startswith('wudangdexiaodoashi/')
    actual_ref=refs[0]
    old=GPU.parents[2]/'u_re/v01/experiments/action_priority_01/real_gemma_abba01/collect.py'
    source=old.read_text(encoding='utf-8').replace('from .GPU_NOTEBOOK import HERE,ROOT,SLUG','')
    source=source.replace("HERE/'execution/HTTP_RECEIPT.json'","RECEIPT")
    source=source.replace('u_re_actionfirst_abba01.zip',f'meer-v01-gpu-batch{batch}.zip')
    source=source.replace("len(meta['model_data_sources'] or []) == 1", "meta['model_data_sources']==['google/gemma-4/Other/gemma-4-31b-it-qat-w4a16-ct/2']")
    ns=dict(HERE=directory,ROOT=GPU.parents[2],SLUG=actual_ref,RECEIPT=receipts[0],__file__=str(old),__name__='MEER_readonly_collector')
    exec(compile(source,str(old),'exec'),ns)
    ns['collect'](PRIVATE/f'batch{batch:02d}')
    binding=directory/'ACTUAL_RESOURCE_BINDING.json'
    if not binding.exists():
        save(binding,dict(Notebook_id=receipt['Notebook_id'],version=1,intended_ref=f'wudangdexiaodoashi/meer-v01-gpu-batch{batch:02d}',actual_ref=actual_ref,
             source='Actual HTTP200 receipt + CLI returned owner/ref; exact source/payload/version/ID independently checked by collector',
             slug_difference='Kaggle derived slug from title; original dispatch intent untouched; no repeat save'))

if __name__=='__main__':
    import sys
    collect(int(sys.argv[1]))
