"""Import path binding for the locked public Requests src-layout snapshots."""
def source_paths(repo):
 return ['/workspace/src','/workspace','/opt/approved'] if repo=='psf/requests' else None

def bind_command(repo,command):
 paths=source_paths(repo)
 return ('export PYTHONPATH='+':'.join(paths)+'; '+command) if paths else command
