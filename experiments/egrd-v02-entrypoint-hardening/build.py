"""Repackage frozen V0.1 implementation with identical explicit entrypoint guidance."""
import hashlib,io,json,zipfile
from pathlib import Path
D=Path(__file__).resolve().parent;OLD=D.parent/'egrd-v01-12b'
sha=lambda b:hashlib.sha256(b).hexdigest()
def main():
 models=json.loads((D/'MODEL_CONFIGURATIONS.json').read_bytes());rows={}
 prefix=(D/'FIRST_ACTION.md').read_bytes()
 base=(D/'inputs/s0/system.md').read_bytes().replace(b'gemma-4-31b-it-qat-w4a16-ct',b'the declared Gemma model')
 assert sha((D/'inputs/s0/system.md').read_bytes())=='5f43c3a546c4c21765aff5e09a92126b1bb104b6e8423b269364a0b8f286a7ce'
 prompt=prefix+base
 for arm,size in [('A','12b'),('B','12b'),('C','31b'),('D','31b')]:
  with zipfile.ZipFile(OLD/'packages'/f'{arm}.zip') as z:files={n:z.read(n) for n in z.namelist()}
  files['prompts/system.md']=prompt
  files['skills/egrd-repair/SKILL.md']+=b'\nEntrypoint: load_skill then run_skill_script with op=init before repository work. Failure/advisory is not activation; never fabricate a contract. All Issue fields and provenance remain required.\n'
  out=io.BytesIO()
  with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
   for name,raw in sorted(files.items()):
    info=zipfile.ZipInfo(name,(2026,11,3,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,raw)
    p=D/'packages'/arm/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
  raw=out.getvalue();(D/'packages'/f'{arm}.zip').write_bytes(raw)
  rows[arm]=dict(model=models[size]['alias'],active=arm in ['B','D'],sha256=sha(raw),members={n:sha(b) for n,b in files.items()})
 m=json.loads((OLD/'PACKAGE_MANIFEST.json').read_bytes());m.update(arms=rows,execution_mode='PROMPT_ENFORCED_OPTIONAL_EXECUTION',entrypoint_prompt_sha256=sha(prompt),preserved_core_sha256=sha((D/'core.py').read_bytes()),baseline_definition='Matched-interface control; all four share FIRST ACTION guidance. A/C inert Skill remains non-activation, B/D unchanged executable V0.1 core. Not exact frozen S0.')
 (D/'PACKAGE_MANIFEST.json').write_text(json.dumps(m,indent=2)+'\n')
 print('BUILT_FOUR_PACKAGES_NO_DISPATCH')
if __name__=='__main__':main()
