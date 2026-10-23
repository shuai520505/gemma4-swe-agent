"""External SCRIPTED_ONLY transport; never present in production package."""
import base64,types,json
from pathlib import Path
from harness_v2.evidence import atomic_json
original=types.ModuleType('REUSED_CPU_ONLY')
code=base64.b64decode('ORIGINAL_CPU_TRANSPORT_BASE64').decode()
code=code.replace('actions=iter([','actions=[').replace("('submit_patch',{}),'End.'])","('submit_patch',{}),'End.']")
code=code.replace("('edit_file',dict(filepath=", "('write_file',dict(filepath='owned-scratch.txt',content='Owned fixture')),('edit_file',dict(filepath=")
code=code.replace("command='python3 checks.py && git diff --check && git diff'","command='python3 checks.py && rm owned-scratch.txt && git diff --check && git diff'")
code=code.replace("action=next(actions,'End.')","action=actions[(len(calls)-1)%7]")
exec(compile(code,'<External-owned-HTTP-fixture>','exec'),original.__dict__)
class CPUTransport(original.CPUTransport):
    def verify(self,output,records):
        assert len(records)==2 and len(self.calls)==14
        schemas=[];generations=[];prompts=[]
        for i,arm in enumerate(('A','B'),1):
            d=Path(output)/f'runs/{i:02d}-ure_gpu03_owned-{arm}'
            result=json.loads((d/'official_result.json').read_bytes());agent=json.loads((d/'agent/agent_result.json').read_bytes());proof=json.loads((d/'COMPILED_PROMPT_EVIDENCE.json').read_bytes())
            assert result['resolved'] and result['test_exit_code']==0 and agent['patch_submitted'] and agent['patch_bytes']>0 and records[i-1]['worker']['allow_next_run']
            assert proof['instruction_visible_in_all_actual_HTTP_requests'] and proof['actual_HTTP_requests']==7
            schemas.append(proof['tools_schema_sha256']);prompts.append(proof['instruction_sha256']);generations.append(proof['compiled'][0]['generation'])
            events=[json.loads(x) for x in (d/'agent/adk_events.jsonl').read_bytes().splitlines()]
            tools={p['function_response']['name'] for e in events for p in e.get('event',{}).get('content',{}).get('parts',[]) if p.get('function_response')}
            assert tools=={'get_status','run_command','read_file','edit_file','write_file','submit_patch'}
            assert b'owned-scratch.txt' not in (d/'final.patch').read_bytes()
            assert (d/'verifier/phase2.junit.xml').is_file()
        assert schemas[0]==schemas[1] and generations[0]==generations[1] and prompts[0]!=prompts[1]
        atomic_json(Path(output)/'CPU_TRANSPORT_PROOF.json',dict(CPU_MODEL='SCRIPTED_ONLY',HTTP_requests=14,tool_results_returned_to_model=True,real_Gemma_requests=0,both_candidates_verified=True,six_tools_executed=True,tools_schema_sha256=schemas[0],generation=generations[0],instruction_sha256=prompts))
