"""Fetch first two ranked public base snapshots; no tests or fixes are read/run."""
import io
import json
import tarfile

import requests

from .cli_recovery import HERE, PRIVATE, sha


def run():
    pool=json.loads((HERE/'EXTERNAL_SOURCE_LOCK.json').read_bytes())
    records=[]
    for row in pool['ranked_metadata'][:2]:
        url=f"https://codeload.github.com/{row['repo']}/tar.gz/{row['base_commit']}"
        response=requests.get(url,proxies={'https':'http://127.0.0.1:7890'},timeout=90,stream=True)
        response.raise_for_status()
        data=bytearray()
        for chunk in response.iter_content(1024*1024):
            data.extend(chunk)
            if len(data)>64*1024*1024:raise ValueError('Public snapshot size budget exceeded')
        raw=bytes(data)
        destination=PRIVATE/'external-sources/snapshots'/f"{row['instance_id']}.tgz"
        destination.parent.mkdir(parents=True,exist_ok=True)
        with destination.open('xb') as file:file.write(raw)
        with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as archive:
            names=archive.getnames()
            assert all(not n.startswith('/') and '..' not in n.split('/') for n in names)
            roots={n.split('/')[0] for n in names}; assert len(roots)==1
            root=next(iter(roots));assert root.endswith(row['base_commit'])
            licenses=[m for m in archive.getmembers() if m.isfile() and
                len(m.name.split('/'))==2 and m.name.split('/')[-1].lower().startswith(('license','copying'))]
            assert licenses
            license_hashes={m.name.split('/')[-1]:sha(archive.extractfile(m).read()) for m in licenses}
        records.append(dict(**row,source_url=url,snapshot_sha256=sha(raw),snapshot_bytes=len(raw),
            archive_root=root,path_names_safe=True,extracted=False,source_tests_read=False,
            license_file_hashes=license_hashes,baseline='NOT_RUN_DOCKER_UNAVAILABLE',admission='NOT_ADMITTED'))
    output=dict(source_lock_sha256=sha((HERE/'EXTERNAL_SOURCE_LOCK.json').read_bytes()),
        first_ranked_only=True,selection_uses_model_results=False,records=records,
        admitted_count=0,native_results=None)
    (HERE/'EXTERNAL_SNAPSHOT_CHECKS.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf8',newline='\n')
    print('Verified first two ranked public snapshots and license-file identities; no admission or baseline.')


if __name__=='__main__':run()
