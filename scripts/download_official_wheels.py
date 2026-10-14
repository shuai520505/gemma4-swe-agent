"""Fetch pinned official artifacts over verified HTTPS; validate retrieved hashes."""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    args.directory.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(Path(__file__).with_name('official_wheels.json').read_text())
    for item in manifest:
        target = args.directory / item['filename']
        if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() == item['sha256']:
            continue
        with urllib.request.urlopen(item['url'], timeout=60) as response:
            data = response.read()
        if hashlib.sha256(data).hexdigest() != item['sha256']:
            raise ValueError(f'official wheel changed: {target.name}; inspect upstream, do not bypass')
        target.write_bytes(data)
        print(f'Verified {target.name}')


if __name__ == '__main__':
    main()
