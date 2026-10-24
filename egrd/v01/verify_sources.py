"""Read-only audit of pinned organizer files and immutable candidate archives."""
import json
import zipfile
from audit import ROOT, PARENT, HERE, sha, write

CANDIDATES = {
 'S0':'candidates/s0/submission.zip',
 'NoEGV':'u_re/v01/submission_noegv.zip',
 'Full':'u_re/v01/submission_full.zip',
 'ActionFirst':'u_re/v01/experiments/action_priority_01/submission_action_v01.zip',
 'EGR':'u_re/v04/experiments/evidence_guided_repair_01/submission_egr_v04.zip',
 'MEER_A':'meer/v01/submission_A.zip', 'MEER_B':'meer/v01/submission_B.zip', 'MEER_C':'meer/v01/submission_C.zip',
}
EXPECTED = {
 'NoEGV':'2705679a74456937d8c63127fc34df9c99a28446f9bd23c23d56650b91602608',
 'Full':'887da066341bb1278ba298894f488bba8e7a3bd09ae5f4417e36a1a51f8ad821',
 'ActionFirst':'70af6921a3366e3801efe58fe06586d13189fdf044d4fd998faa62ea7e0fb1c8',
 'EGR':'07263740c5ee22bf6611d7fa31dafbc84d7fb50288d22355b9201cd6954a6840',
 'MEER_A':'07263740c5ee22bf6611d7fa31dafbc84d7fb50288d22355b9201cd6954a6840',
 'MEER_B':'d962044f264d8f36aea6263abf4dcdb118d5755e82a91cb9b2bd0bc1f6f7c9cd',
 'MEER_C':'8dd48fee0c96424a40ed47512f0d788d9b13518e7d73395bd89d2fb07204eb83',
}

def run():
    report={'candidates':{},'organizer':{},'formal_scores':{},'boundary':'Read-only local evidence; no Kaggle execution or status mutation.'}
    contents={}
    for label,location in CANDIDATES.items():
        p=ROOT/location; h=sha(p.read_bytes())
        if label in EXPECTED and EXPECTED[label]!=h:raise ValueError('Frozen candidate mismatch')
        with zipfile.ZipFile(p) as z:
            assert z.testzip() is None
            contents[label]={n:z.read(n) for n in z.namelist() if not n.endswith('/')}
        report['candidates'][label]={'path':location,'sha256':h,'members':{n:sha(b) for n,b in contents[label].items()}}
    for label in ['Full','ActionFirst','EGR']:
        for n in ['agent.yaml','eval_config.yaml']:assert contents[label][n]==contents['NoEGV'][n]
    assert contents['EGR']==contents['MEER_A']
    bc=[n for n in set(contents['MEER_B'])|set(contents['MEER_C']) if contents['MEER_B'].get(n)!=contents['MEER_C'].get(n)]
    report['MEER_B_C_different_members']=sorted(bc)
    pins=json.loads((ROOT/'meer/v01/OFFICIAL_SOURCE_PINS.json').read_bytes())
    for n,pin in pins.items():
        if n.endswith('.whl'):
            path=PARENT/'gemma4-swe-agent/artifacts/harness-v2/official-wheels'/n
            assert sha(path.read_bytes())==pin['sha256']
            with zipfile.ZipFile(path) as z:
                for member,m in pin['members'].items():assert sha(z.read(member))==m['sha256']
            report['organizer'][n]=pin
    guide=PARENT/'official-inputs/HARNESS_README.md'
    assert sha(guide.read_bytes())==pins['HARNESS_README.md']['sha256']
    report['organizer']['HARNESS_README.md']=pins['HARNESS_README.md']
    formal=PARENT/'private-evidence/formal_score/20261024T064633261982Z/FORMAL_STATUS.json'
    if formal.exists():
        raw=formal.read_bytes();assert sha(raw)=='5742b63aaf2b3e8cb84eaccf3d771d7d54bdff01506e8c3e6c7058b28c467da9'
        observed={str(x['ref']):{'status':x['status'],'public_score':x['publicScore']} for x in json.loads(raw)['submissions'] if str(x['ref']) in ['57261002','57505115','57566588']}
        report['formal_scores']={'source_sha256':sha(raw),'status':'ARCHIVE_IDENTITY_AND_ROWS_VERIFIED','official_rows':observed,'per_task_trajectories':'NOT_AVAILABLE'}
    write(HERE/'SOURCE_AUDIT.json',report)
    print('Immutable candidates, organizer wheels/members, guide and formal archive verified.')

if __name__=='__main__':run()
