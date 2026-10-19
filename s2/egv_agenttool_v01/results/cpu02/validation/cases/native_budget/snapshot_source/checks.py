import app, hashlib, pathlib, sys
print('SOURCE', app.__file__, hashlib.sha256(pathlib.Path(app.__file__).read_bytes()).hexdigest(), flush=True)
print('SYS_PATH', sys.path, flush=True)
print('TARGET', app.accepts(0), flush=True)
assert app.accepts(0) is True, 'TARGET_BOUNDARY'
print('TARGET_PASSED', flush=True)
assert app.accepts(-1) is False, 'OLD_NEGATIVE'
print('OLD_PASSED', flush=True)
