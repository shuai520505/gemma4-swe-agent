"""Resolve declared PEP518 build requirements only from pinned official task wheels."""
from pathlib import Path
from packaging.requirements import Requirement
from packaging.tags import sys_tags
from packaging.utils import canonicalize_name,parse_wheel_filename


def select(requirement,wheels):
    req=Requirement(requirement)
    if req.url:raise ValueError('Direct URL build dependencies are not allowed in offline research admission')
    if req.marker and not req.marker.evaluate():return None
    tags=set(sys_tags());matches=[]
    for path in Path(wheels).glob('*.whl'):
        name,version,build,compatible=parse_wheel_filename(path.name)
        if canonicalize_name(req.name)==name and version in req.specifier and compatible.intersection(tags):
            matches.append((version,path))
    if not matches:raise RuntimeError('No compatible official wheel for declared build requirement '+requirement)
    return max(matches,key=lambda row:row[0])[1]
