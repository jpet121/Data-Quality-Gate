#!/usr/bin/env python3
"""Install only this package's marked guidance and skill; preserve unrelated files."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[1]
NAME = 'evidence-driven-python-build'
START = '<!-- BEGIN evidence-driven-engineering v1 -->'
END = '<!-- END evidence-driven-engineering v1 -->'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def atomic_write(path, data, mode=0o644):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(data)
    try:
        temporary.chmod(mode)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def install(codex_home, skills_root, dry_run=False, package=ROOT):
    codex_home = Path(codex_home).expanduser().absolute()
    skills_root = Path(skills_root).expanduser().absolute()
    global_file = codex_home / 'AGENTS.md'
    if (codex_home / 'AGENTS.override.md').exists():
        raise ValueError('Global AGENTS.override.md exists: review effective precedence before installing')
    skill = skills_root / NAME
    payload = package / 'skills' / NAME
    block = (package / 'guidance/GLOBAL_AGENTS_ADDITION.md').read_bytes().rstrip() + b'\n'
    start, end = START.encode(), END.encode()
    if block.count(start) != 1 or block.count(end) != 1:
        raise ValueError('Invalid package marker block')
    previous = global_file.read_bytes() if global_file.exists() else b''
    if previous.count(start) != previous.count(end) or previous.count(start) > 1:
        raise ValueError('Duplicate or unmatched installed guidance markers')
    if start in previous:
        old_block = previous.split(start, 1)[1].split(end, 1)[0]
        new_block = block.split(start, 1)[1].split(end, 1)[0]
        if old_block != new_block:
            raise ValueError('Managed block differs: review existing authorized guidance before updating')
        desired = previous
    else:
        desired = previous + (b'\n\n' if previous else b'') + block
    owner = skill / '.installation.json'
    if owner.is_symlink():
        raise ValueError('Refusing symlink ownership metadata')
    ownership = json.loads(owner.read_text()) if owner.exists() else {'files': {}}
    if owner.exists() and (ownership.get('name') != NAME or ownership.get('schema_version') != '1.0'):
        raise ValueError('Unrecognized ownership metadata; preserve and review it before installing')
    source_files = {str(p.relative_to(payload)): p.read_bytes() for p in payload.rglob('*') if p.is_file()}
    if not source_files or 'SKILL.md' not in source_files:
        raise ValueError('Incomplete skill payload')
    # Construct and validate the complete plan before changing any destination.
    plan = [(global_file, desired)] + [(skill / rel, data) for rel, data in source_files.items()]
    for path, data in plan:
        if any(part.is_symlink() for part in [path, *path.parents]):
            raise ValueError('Refusing symlink destination: ' + str(path))
        if path != global_file and path.exists() and path.read_bytes() != data:
            relative = str(path.relative_to(skill))
            if ownership.get('files', {}).get(relative) != digest(path.read_bytes()):
                raise ValueError('Existing skill file conflicts or was locally edited: ' + str(path))
    changed = []
    backups = []
    expected = {str(path): digest(data) for path, data in plan}
    for path, data in plan:
        if path.exists() and path.read_bytes() == data:
            continue
        changed.append(str(path))
        if dry_run:
            continue
        if path.exists():
            old = path.read_bytes()
            backup = codex_home / 'knowledge-backups' / NAME / (path.name + '.' + digest(old))
            if not backup.exists():
                atomic_write(backup, old, path.stat().st_mode & 0o777)
            backups.append(str(backup))
        mode = (path.stat().st_mode & 0o777) if path.exists() else 0o644
        atomic_write(path, data, mode)
    ownership_data = json.dumps({'schema_version': '1.0', 'name': NAME,
                                'files': {rel: digest(data) for rel, data in source_files.items()}},
                               indent=2).encode() + b'\n'
    if not dry_run and (not owner.exists() or owner.read_bytes() != ownership_data):
        atomic_write(owner, ownership_data)
    return {'status': 'DRY_RUN' if dry_run else 'INSTALLED', 'global_path': str(global_file),
            'skill_path': str(skill), 'changed_files': changed, 'backups': backups,
            'expected_sha256': expected, 'preserved_existing_global_prefix': desired.startswith(previous),
            'scope': 'Filesystem installation for this Codex home/user skill root; fresh discovery and cross-machine persistence require separate checks'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--codex-home', type=Path,
                        default=Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))))
    parser.add_argument('--skills-root', type=Path, default=Path.home() / '.agents/skills')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    result = install(args.codex_home, args.skills_root, args.dry_run)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
