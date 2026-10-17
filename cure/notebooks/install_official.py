import glob
os.environ.update(TRANSFORMERS_NO_TF='1',TRANSFORMERS_NO_FLAX='1',TRANSFORMERS_OFFLINE='1',HF_HUB_OFFLINE='1',LITELLM_LOCAL_MODEL_COST_MAP='True',LITELLM_TELEMETRY='False',OTEL_SDK_DISABLED='true',PYTHONIOENCODING='utf-8')
for pattern in ('/usr/local/lib/python*/dist-packages/*cutlass*.pth','/usr/local/lib/python*/site-packages/*cutlass*.pth'):
    for path in glob.glob(pattern): Path(path).unlink(missing_ok=True)
wheels=list(Path('/kaggle/input').rglob('swegemma-0.2.11-py3-none-any.whl'))
assert len(wheels)==1
wheelhouse=wheels[0].parent
links=RUN_DIR/'wheelhouse_links'; links.mkdir()
for p in wheelhouse.glob('*.whl'):
    if 'cutlass' in p.name.lower(): continue
    name=p.name.replace('cu128','+cu128') if 'cu128' in p.name and '+' not in p.name else p.name
    (links/name).symlink_to(p)
pins=['swegemma-0.2.11-py3-none-any.whl','adk_submission-0.2.13-py3-none-any.whl','adk_eval_core-0.1.0-py3-none-any.whl','google_adk-1.36.1-py3-none-any.whl','google_genai-2.11.0-py3-none-any.whl']
try:
    with (RUN_DIR/'installation.log').open('x') as log:
        # Match official Getting Started: curated wheels, no dependency resolver.
        subprocess.run([sys.executable,'-m','pip','install','--no-index','--no-deps','--force-reinstall']+
            sorted(str(p) for p in links.glob('*.whl')),stdout=log,stderr=subprocess.STDOUT,check=True,timeout=1800)
finally:
    shutil.rmtree(links)
