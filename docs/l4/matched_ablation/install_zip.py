"""Checksum-verified, non-overwriting installer; also the ZIP's __main__.py."""
import argparse
import hashlib
import json
import stat
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath

BASE = '8d3184ec68877413f61d106541ae9b36fec34353'
PREFIXES = ('scripts/l4/tnsm_revision/matched_ablation/',
            'test/l4/tnsm_revision/matched_ablation/',
            'docs/l4/matched_ablation/')


def install(archive, repo):
    repo = repo.expanduser().resolve()
    result = subprocess.run(['git', '-C', str(repo), 'rev-parse', '--show-toplevel'],
                            capture_output=True, text=True)
    if result.returncode or Path(result.stdout.strip()).resolve() != repo:
        raise ValueError('Specify the root of the separate experiment worktree.')
    if subprocess.run(['git', '-C', str(repo), 'merge-base', '--is-ancestor', BASE, 'HEAD'],
                      capture_output=True).returncode:
        raise ValueError('The required revision commit is not an ancestor of this checkout.')
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        if len(names) != len(set(names)):
            raise ValueError('Duplicate ZIP member.')
        for info in z.infolist():
            p = PurePosixPath(info.filename)
            if p.is_absolute() or '..' in p.parts or '\\' in info.filename or info.is_dir() or stat.S_ISLNK(info.external_attr >> 16):
                raise ValueError('Unsafe ZIP member.')
        manifest = {}
        for line in z.read('SHA256SUMS.txt').decode().splitlines():
            sha, name = line.split('  ', 1)
            if name in manifest or len(sha) != 64:
                raise ValueError('Invalid checksum manifest.')
            manifest[name] = sha
        if set(names) != set(manifest) | {'SHA256SUMS.txt'}:
            raise ValueError('Unbound ZIP members.')
        for name, expected in manifest.items():
            if hashlib.sha256(z.read(name)).hexdigest() != expected:
                raise ValueError('Package checksum mismatch: ' + name)
        info = json.loads(z.read('PACKAGE_INFO.json'))
        if info['required_ancestor'] != BASE:
            raise ValueError('Unexpected package lineage.')
        planned = []
        for name in names:
            if not name.startswith('payload/'):
                continue
            relative = name.removeprefix('payload/')
            if not relative.startswith(PREFIXES):
                raise ValueError('Unexpected install destination.')
            target = repo / relative
            if not target.resolve().is_relative_to(repo) or target.exists() or target.is_symlink():
                raise ValueError('Destination exists or is unsafe: ' + relative)
            planned.append((name, target))
        if not planned:
            raise ValueError('No payload files.')
        # Check every path/hash before creating any file. Never overwrite.
        for name, target in planned:
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as f:
                f.write(z.read(name))
    print('Installed files:', len(planned))
    print('Provider calls made: 0')
    print('Existing evidence and gateway services unchanged.')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', required=True, type=Path)
    p.add_argument('--archive', type=Path, default=Path(sys.argv[0]))
    a = p.parse_args()
    try:
        install(a.archive, a.repo)
    except (ValueError, OSError, KeyError, zipfile.BadZipFile) as error:
        raise SystemExit('Installation stopped: ' + str(error))


if __name__ == '__main__':
    main()
