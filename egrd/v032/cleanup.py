"""Recover only exact experiment-owned roots after a killed worker; no retries."""
import json
from pathlib import Path


def recover(directory):
    from egrd.v0311.lifecycle import release_owned
    from u_re.v01.experiments.action_priority_01.integrated_cpu_01.CHROOT_TASK_RUNTIME import kill_owned
    directory=Path(directory).resolve();records=[]
    names=['baseline/trusted-roots']+[f'{arm}/{suffix}' for arm in ('A','B') for suffix in ('roots','trusted/trusted-roots')]
    for name in names:
        base=directory/name;registry=base/'owned_uids.json'
        if not registry.exists():continue
        assert not registry.is_symlink() and registry.resolve().is_relative_to(directory)
        rows=json.loads(registry.read_bytes());assert rows['kind']=='URE_OWNED_UID_REGISTRY_V1'
        for entry in rows['entries']:
            root=Path(entry['root']);lease=Path(entry['lease'])
            assert root.resolve().parent==base.resolve() and not root.is_symlink()
            assert lease==Path('/tmp/ure_owned_uid_leases')/str(entry['uid'])
            if lease.exists():records.append(release_owned(entry,base,kill_owned))
            else:assert not root.exists(),'Residual root without verifiable ownership lease'
    return dict(complete=True,recovered=records)
