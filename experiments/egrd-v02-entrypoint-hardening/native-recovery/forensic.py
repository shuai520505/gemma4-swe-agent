"""Read-only CPU02 autopsy and strict trust re-audit. No service/package execution."""
import ast,hashlib,json,re,sys,zipfile,xml.etree.ElementTree as ET
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parent;D=R.parent;ROOT=D.parents[1]
sys.path.insert(0,str(D))
from result_contract import native_execution_check
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
load=lambda p:json.loads(Path(p).read_bytes())
def write(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n',encoding='utf8')

def autopsy():
 trusted=D/'cpu02-evidence/worker/trusted';xml=trusted/'native-junit-0.xml';cases=ET.parse(xml).getroot().findall('.//testcase')
 rows=[]
 for index,c in enumerate(cases):
  for kind in ['error','failure']:
   node=c.find(kind)
   if node is None:continue
   trace=node.text or '';message=node.get('message') or '';joined=trace+'\n'+message
   group='HTTPBIN_PROVIDER_UNRESOLVED' if "recursive dependency involving fixture 'httpbin'" in joined else 'HTTPBIN_SECURE_PROVIDER_UNRESOLVED' if "recursive dependency involving fixture 'httpbin_secure'" in joined else 'NETWORK_CONFINEMENT_EACCES' if '[Errno 13] Permission denied' in joined and 'NewConnectionError' in joined else 'UNCLASSIFIED'
   rows.append(dict(case_index=index,name=c.get('name'),classname=c.get('classname'),kind=kind,group=group,trace_sha256=hashlib.sha256(trace.encode()).hexdigest(),message_sha256=hashlib.sha256(message.encode()).hexdigest(),evidence=f'cpu02-evidence/worker/trusted/native-junit-0.xml:testcase_index_0based={index}',trace_excerpt=trace[-1800:] if kind=='failure' else trace))
 agent_runtime=next((D/'cpu02-evidence/worker').glob('task_runtime_*.json'));native_runtime=next(trusted.glob('task_runtime_*.json'))
 a=load(agent_runtime);n=load(native_runtime);wheels=[r['name'] for r in n['wheels']]
 commands=load(trusted/'NATIVE_COMMANDS.json');native_command=next(r['command'] for r in commands if '--junitxml=' in r['command'])
 child=ROOT/'outputs/r12_redispatch/mount-mirror/source/u_re/v01/experiments/action_priority_01/integrated_cpu_01/chroot_child.py'
 policy=child.with_name('landlock_exec.py');tree=ast.parse(child.read_text(encoding='utf8'))
 env=next(x.value for x in ast.walk(tree) if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='env' for t in x.targets))
 envkeys=[k.arg for k in env.keywords];proxykeys=[k for k in envkeys if k.lower() in ['http_proxy','https_proxy','all_proxy','no_proxy']]
 cleanup=load(D/'cpu02-evidence/worker/CLEANUP.json');native_cleanup=load(trusted/'CLEANUP.json')
 original=load(trusted/'NATIVE_RESULT.json');receipt=load(D/'cpu02-evidence/worker/SESSION_RESULT.json');done=load(D/'cpu02-evidence/worker/worker_done.json')
 sourceguard=load(trusted/'VERIFICATION_SOURCE_GUARD.json')
 result=dict(observed_at_utc=datetime.now(timezone.utc).isoformat(),source_commit='9ef032ab23335cb5a09c4937d7962205f5962f79',scope='Original actual Linux CPU02 artifacts plus read-only source inspection; no new Native run',cases=len(cases),groups={g:sum(r['group']==g for r in rows) for g in sorted({r['group'] for r in rows})},records=rows,xml_sha256=sha(xml),Native_sha256=sha(trusted/'NATIVE_RESULT.json'),raw_resolved=original['resolved'],raw_exit_code=original['test_exit_code'],native_hash_matches_receipts=receipt['native_result_sha256']==done['native_result_sha256']==sha(trusted/'NATIVE_RESULT.json'),wheels=dict(count=len(wheels),names=wheels,provider_in_approved_wheels=any(re.match(r'(pytest[-_]httpbin|httpbin)[-_]',s,re.I) for s in wheels),Agent_Native_identical=a['wheels']==n['wheels']),environment=dict(child_sha256=sha(child),policy_sha256=sha(policy),explicit_keys=envkeys,proxy_keys=proxykeys,network_policy='AF_INET/AF_INET6 creation and connect denied; unchanged',Agent_Native_shared_launcher=True),source_binding=dict(Agent=load(D/'cpu02-evidence/worker/REQUESTS_SOURCE_BINDING.json'),Native_command=native_command,Native_trace_references_workspace_src=all('src/requests/adapters.py' in r['trace_excerpt'] for r in rows if r['kind']=='failure'),guard=sourceguard,exact_pre_patch_Agent_Native_byte_parity='NOT_RUN; original binding is evidenced, complete cross-workspace fingerprint was not recorded'),cleanup=dict(Agent=cleanup['complete'],Native=native_cleanup['complete'],fixture_teardown='NOT_RUN',fixture_teardown_reason='Provider resolution failed before startup'),not_executed=dict(HTTP_startup='NOT_RUN',HTTPS_startup='NOT_RUN',TLS_handshake='NOT_RUN',port_conflict='NOT_RUN',DNS_resolution='NOT_RUN',fixture_crash_recovery='NOT_RUN'),version=dict(required_pytest_httpbin='2.0.0',actual_registered_provider='ABSENT_CONFIRMED_BY_FIXTURE_RESOLUTION',actual_installed_version='UNKNOWN_NOT_DIRECTLY_PROBED',approved_pytest='8.4.2',repository_dev_pytest_constraint='>=2.8.0,<=6.2.5',compatibility_with_provider='NOT_RUN'),status='BLOCKED_INFRASTRUCTURE')
 with zipfile.ZipFile(D/'cpu02-output/egrd-v02-cpu-hardening02.zip') as archive:
  result['archive_matches_extracted_evidence']=all((D/'cpu02-evidence'/info.filename).is_file() and (D/'cpu02-evidence'/info.filename).read_bytes()==archive.read(info) for info in archive.infolist() if not info.is_dir())
 result['session_hash_matches_done']=done['session_result_sha256']==sha(D/'cpu02-evidence/worker/SESSION_RESULT.json')
 result['cleanup_hash_matches_done']=done['cleanup_sha256']==sha(D/'cpu02-evidence/worker/CLEANUP.json')
 return result

if __name__=='__main__':
 result=autopsy();write(R/'AUTOPSY.json',result)
 trust=native_execution_check(D/'cpu02-evidence/worker/trusted/NATIVE_RESULT.json')
 write(D/'NATIVE_TRUST_AUDIT.json',dict(status='BLOCKED_INFRASTRUCTURE',trust_passed=False,Native_execution_integrity=trust,hash_matches_receipts=result['native_hash_matches_receipts'],cleanup=result['cleanup'],source_binding=result['source_binding'],new_Linux_acceptance='NOT_RUN',raw_CPU02_receipt_preserved=True,missing_capabilities=['Approved registered pytest-httpbin2.0.0/httpbin provider dependency closure','Confinement-compatible real local HTTP/HTTPS sockets','Real timeout behavior required by four10.255.255.1 tests'],GPU_dispatched=False))
 print(json.dumps(dict(status=result['status'],cases=result['cases'],groups=result['groups'],receipt_hashes_match=result['native_hash_matches_receipts'])))
