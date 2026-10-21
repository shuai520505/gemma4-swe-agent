"""Frozen ZIP checks and public-task projection; no network or evaluator text."""
import hashlib,json,re,zipfile
from pathlib import Path,PurePosixPath
ZIPS={'noegv':'2705679a74456937d8c63127fc34df9c99a28446f9bd23c23d56650b91602608',
      'full':'887da066341bb1278ba298894f488bba8e7a3bd09ae5f4417e36a1a51f8ad821'}
MEMBERS={'agent.yaml','eval_config.yaml','prompts/system.md'}
TOOLS=['get_status','run_command','read_file','edit_file','write_file','submit_patch']

def sha(raw):return hashlib.sha256(raw).hexdigest()
def write(name,data):
    (HERE/name).write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

def candidate(path,expected):
    assert sha(Path(path).read_bytes())==expected,'Candidate ZIP drift'
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        assert set(z.namelist())==MEMBERS and len(z.namelist())==3
        for n in z.namelist():
            assert not PurePosixPath(n).is_absolute() and '..' not in PurePosixPath(n).parts
        agent=z.read('agent.yaml').decode();prompt=z.read('prompts/system.md').decode()
        assert 'agent_tool' not in agent and 'sub_agents' not in agent
        assert 'agent_class: LlmAgent' in agent
        listed=re.findall(r'^\s*-\s*(\w+)\s*$',agent,re.M)
        assert listed==TOOLS
        assert not any(s in prompt for s in ('evaluator_test_text','phase2.junit','TaskResult','test_patch'))
        return dict(zip_sha256=expected,members={n:sha(z.read(n)) for n in z.namelist()},
                    CRC_valid=True,single_LlmAgent=True,tools=listed)

def agent_input(record):
    """Permit only the official public task projection, never an entire evaluator record."""
    allowed={'instance_id','repo','base_commit','problem_statement'}
    if set(record)!=allowed or any(not isinstance(v,str) or not v for v in record.values()):
        raise ValueError('Agent input must be a public-task projection')
    return dict(record)

