"""External CPU-only HTTP transport; never included in production ZIP."""
import inspect,json
from pathlib import Path
import base64,types
original=types.ModuleType('CPU_ONLY_REUSED_ORIGINAL')
_source=base64.b64decode('ORIGINAL_CPU_TRANSPORT_BASE64').decode()
_source=_source.replace('actions=iter([','actions=[').replace("('submit_patch',{}),'End.'])","('submit_patch',{}),'End.']").replace("action=next(actions,'End.')","action=actions[(len(calls)-1)%6]")
exec(compile(_source,'<CPU-only-original-transport>','exec'),original.__dict__)
from harness_v2.evidence import atomic_json

class CPUTransport(original.CPUTransport):
    def start(self,data,output):
        return original.CPUTransport.start(self,data,output)
    def verify(self,output,records):
        assert len(records)==2 and len(self.calls)==12
        for i,arm in enumerate(('A','B'),1):
            d=Path(output)/f'runs/{i:02d}-ure_gpu03_owned-{arm}'
            result=json.loads((d/'official_result.json').read_bytes());agent=json.loads((d/'agent/agent_result.json').read_bytes())
            cfg=json.loads((d/'runtime_config.json').read_bytes());cap=16384 if arm=='A' else 8192
            assert result['resolved'] and result['test_exit_code']==0 and agent['patch_submitted'] and agent['patch_bytes']>0
            assert records[i-1]['worker']['allow_next_run'] and cfg['generation']['max_output_tokens']==cap and cfg['generation']['thinking_config']['thinking_budget']==4096
            requests=self.calls[(i-1)*6:i*6]
            assert all(b.get('max_completion_tokens',b.get('max_tokens'))==cap and b['thinking_token_budget']==4096 for b in requests)
            assert any(m.get('role')=='tool' for b in requests for m in b['messages'])
            assert (d/'verifier/phase2.junit.xml').is_file()
        atomic_json(Path(output)/'CPU_TRANSPORT_PROOF.json',dict(CPU_MODEL='SCRIPTED_ONLY',HTTP_requests=12,tool_results_returned_to_model=True,real_Gemma_requests=0,both_policies_verified=True))
