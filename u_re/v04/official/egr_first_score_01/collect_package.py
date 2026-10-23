"""Read-only ID mapping and version/source/output verification; never saves."""
import json,types,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];ID=json.loads((HERE/'execution/HTTP_RECEIPT.json').read_bytes())['Notebook_id']
OWNER='wudangdexiaodoashi'
def collect():
    from kaggle import api
    from kagglesdk.kernels.types.kernels_api_service import ApiListKernelsRequest,KernelsListViewType,KernelsListSortType
    number=len(list((ROOT.parent/'private-evidence/u_re_v04_egr_first_official_score').glob('read-*')))+1;assert number<=5
    dest=ROOT.parent/'private-evidence/u_re_v04_egr_first_official_score'/f'read-{number:02d}';dest.mkdir(parents=True,exist_ok=False)
    mapping=HERE/'RESOURCE_MAPPING.json'
    if not mapping.exists():
        found=[]
        with api.build_kaggle_client() as client:
            for page in range(1,6):
                q=ApiListKernelsRequest();q.user=OWNER;q.group=KernelsListViewType.PROFILE;q.sort_by=KernelsListSortType.DATE_CREATED;q.page_size=100;q.page=page;q.kernel_type='all';q.language='all';q.output_type='all';q.search=''
                rows=client.kernels.kernels_api_client.list_kernels(q)
                # Profile records omit numeric IDs (0). Exact platform title/ref
                # locates a candidate only; GetKernel below must prove the ID.
                found.extend(x for x in rows.kernels or [] if x.id==ID or
                    (x.id==0 and x.ref==OWNER+'/u-re-egr-v04-first-official-score'))
                if found or len(rows.kernels or [])<100:break
        assert len(found)==1
        ref=found[0].ref
        if ref.startswith('https://www.kaggle.com/code/'):ref=ref.removeprefix('https://www.kaggle.com/code/')
        assert ref.startswith(OWNER+'/') and len(ref.split('/'))==2
        with mapping.open('x',encoding='utf-8') as f:json.dump(dict(expected_id=ID,profile_returned_id=found[0].id,candidate_ref=ref,actual_ref=ref,requested_ref=json.loads((HERE/'BUILD.json').read_text(encoding='utf-8'))['slug'],reason='Exact observed platform title-derived ref. Profile IDs may be0; GetKernel must independently prove ID/source/config/version before collection. No new save.'),f,indent=2)
    ref=json.loads(mapping.read_text(encoding='utf-8'))['actual_ref']
    original=ROOT/'u_re/v01/experiments/fastapi_pilot_01/attempts/cpu02/reconciliation_01/recover.py'
    text=original.read_text(encoding='utf-8').replace("payload=__import__('base64').b64decode(",'raw=base64.b64decode(')
    old="item.file_name.endswith('.zip') and 'cpu02/' in item.file_name and '/source/' not in item.file_name"
    assert old in text;text=text.replace(old,"item.file_name == 'submission.zip'")
    m=types.ModuleType('package_readonly_recovery');m.__file__=str(original);exec(compile(text,str(original),'exec'),m.__dict__)
    m.HERE=dest;m.CPU02=HERE;m.OWNER=OWNER;m.SLUG=ref.split('/')[1];m.REF=ref;m.ID=ID
    freeze=HERE/'BUILD_FREEZE.json'
    if not freeze.exists():shutil.copyfile(HERE/'BUILD.json',freeze)
    m.run(read_latest=True,confirmed_read=True)
if __name__=='__main__':collect()
