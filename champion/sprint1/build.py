"""Three single-factor archives from exact original S0 members; no inference."""
import hashlib
import io
import json
from pathlib import Path
import zipfile
import difflib

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
PRIVATE=Path.home()/'.codex/private-evidence/champion_sprint1'
S0_SHA='3303d6e1dd246d3861910701beb580c8d9a165ea1eb1c1a13d8c8ba9d6efd4f9'
NAMES=('C1_BUDGET','C2_CONTEXT','C3_TEST_AWARE')

def sha(body):return hashlib.sha256(body).hexdigest()
def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes((json.dumps(value,indent=2,sort_keys=True)+'\n').encode())

def archive(files):
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for name,body in sorted(files.items()):
            info=zipfile.ZipInfo(name,(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=0o100644<<16;z.writestr(info,body)
    return stream.getvalue()

def base():
    raw=(ROOT/'candidates/s0/submission.zip').read_bytes();assert sha(raw)==S0_SHA
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        assert z.testzip() is None
        files={n:z.read(n) for n in z.namelist()}
    assert set(files)=={'agent.yaml','eval_config.yaml','prompts/system.md'}
    return files

def build():
    original=base();manifest=dict(S0_sha256=S0_SHA,candidates={})
    for name in NAMES:
        files=original.copy()
        if name=='C2_CONTEXT':files['agent.yaml']+=b'\ngenerate_content_config:\n  max_output_tokens: 8192\n'
        else:files['prompts/system.md']+=b'\n\n'+(HERE/(name+'.md')).read_bytes()
        raw=archive(files);folder=HERE/'candidates'/name;folder.mkdir(parents=True,exist_ok=True)
        (folder/'submission.zip').write_bytes(raw)
        changed=[n for n in sorted(files) if files[n]!=original[n]]
        assert changed==(['agent.yaml'] if name=='C2_CONTEXT' else ['prompts/system.md'])
        diff=[]
        for n in changed:
            diff.extend(difflib.unified_diff(original[n].decode().splitlines(),files[n].decode().splitlines(),
                fromfile='S0/'+n,tofile=name+'/'+n,lineterm=''))
        (folder/'DIFF.patch').write_text('\n'.join(diff)+'\n',encoding='utf8',newline='\n')
        row=dict(sha256=sha(raw),bytes=len(raw),members={n:sha(b) for n,b in files.items()},
            changed_members=changed,official_Compiler='NOT_RUN',model='gemma-4-31b-it-qat-w4a16-ct',
            generation_expected={'max_output_tokens':8192 if name=='C2_CONTEXT' else 16384,'thinking_config':{'thinking_budget':4096}},
            evaluation={'max_time_minutes':5.0,'max_tool_calls':60,'timeout_seconds':120},
            mechanism='Prompt adoption/decision guidance only' if name!='C2_CONTEXT' else 'Output cap only; no custom Guard')
        write(folder/'MANIFEST.json',row);manifest['candidates'][name]=row
    write(HERE/'CANDIDATE_MANIFEST.json',manifest)
    print(json.dumps({n:r['sha256'] for n,r in manifest['candidates'].items()},indent=2))
    return manifest

if __name__=='__main__':build()
