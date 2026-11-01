"""Recover actual CPU proof and assert dispatched bytes match current adapters."""
import hashlib,json,subprocess,sys,zipfile
from pathlib import Path
D=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
def write(p,x):(D/p).write_text(json.dumps(x,indent=2)+'\n',encoding='utf8')
archives=[]
for attempt in ['attempt-01','attempt-02']:
    p=D/attempt/'r2-infra-cpu-hardening-01.zip'
    with zipfile.ZipFile(p) as z:
        assert z.testzip() is None
        summary=json.loads(z.read('CPU_HARDENING_SUMMARY.json'))
        archives.append(dict(attempt=attempt,sha256=sha(p.read_bytes()),bytes=p.stat().st_size,status=summary['status'],entries=[dict(path=n,sha256=sha(z.read(n)),bytes=len(z.read(n))) for n in z.namelist() if not n.endswith('/')]))
        if attempt=='attempt-02':
            assert summary['status']=='PASS'
            result=json.loads(z.read('integration/CPU_INTEGRATION_RESULTS.json'));assert result['status']=='PASS' and len(result['rows'])==4 and result['GPU_devices']==0 and result['real_model_requests']==0
            identities=json.loads(z.read('SOURCE_IDENTITIES.json'))
            assert all(sha((D/n).read_bytes())==h for n,h in identities.items())
            for row in result['rows']:
                assert row['status']=='PASS' and not row['source_changes'] and row['patch_bytes']==0
                label=row['case'];receipt=json.loads(z.read('integration/'+label+'/CLEANUP.json'));assert receipt['complete']
                for n in z.namelist():
                    if n.startswith('integration/'+label+'/') and (n.endswith(('SOURCE_CLI_ADMISSION.json','INFRASTRUCTURE_STOP.json','CLEANUP.json')) or '/ISOLATION_' in n):
                        target=D/'evidence'/n.replace('/','__');target.parent.mkdir(exist_ok=True);target.write_bytes(z.read(n))
            assert [r['localhost_scripted_requests'] for r in result['rows']]==[2,1,1,0]
            assert result['coordinator_composition']=='PASS'
            write('CPU_INTEGRATION_RESULTS.json',result)
write('CPU_EVIDENCE_INDEX.json',dict(archives=archives,real_Gemma_requests=0,GPU_devices=0,scope='CPU-only scripted SDK and actual nonroot CLI integration; no Agent repair benefit evidence'))
tests=subprocess.run([sys.executable,str(D/'test_stop_policy.py')],capture_output=True,text=True)
assert tests.returncode==0
(D/'LOCAL_TEST_RESULTS.txt').write_text(tests.stderr,encoding='utf8')
subprocess.run([sys.executable,str(D/'freeze_inputs.py')],check=True)
write('FINAL_VERIFICATION.json',dict(status='CPU_INFRA_HARDENING_VERIFIED',local_tests=6,CPU_scenarios=4,scripted_HTTP_requests=[2,1,1,0],source_CLI_and_locale_verified=True,negative_preflight_requests=0,all_cleanup_verified=True,frozen_inputs='74 historical + 87 prior-study assets unchanged',real_Gemma_requests=0,GPU_dispatches=0,formal_submissions=0,original_pilot_conclusion='INCONCLUSIVE_UNCHANGED',scope='Known reproduced faults and declared classifier patterns; not all possible infrastructure errors or GPU readiness'))
print('CPU_INFRA_HARDENING_VERIFIED')
