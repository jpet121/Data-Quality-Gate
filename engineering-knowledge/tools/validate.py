#!/usr/bin/env python3
"""Deterministic local validation of guidance, skill links and optional manifest."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import stat

NAME = 'evidence-driven-python-build'


def validate(skill, global_file=None, manifest_root=None):
    skill = Path(skill).resolve()
    text = (skill / 'SKILL.md').read_text()
    assert text.startswith('---\n')
    header, body = text[4:].split('\n---\n', 1)
    fields = dict(line.split(': ', 1) for line in header.splitlines())
    assert fields['name'] == NAME and len(fields['description']) >= 40
    assert 'Use $' + NAME in body and len(body.split()) < 1200
    links = re.findall(r'\[[^\]]+\]\(([^)]+)\)', body)
    assert links
    for rel in links:
        target = (skill / rel.split('#')[0]).resolve()
        assert target.is_relative_to(skill) and target.is_file(), rel
    json.loads((skill / 'templates/completion.json').read_text())
    for path in skill.rglob('*'):
        assert not path.is_symlink()
        if path.is_file():
            assert stat.S_IMODE(path.stat().st_mode) & 0o022 == 0, str(path)
    if global_file:
        global_text = Path(global_file).read_text()
        assert global_text.count('<!-- BEGIN evidence-driven-engineering v1 -->') == 1
        assert global_text.count('<!-- END evidence-driven-engineering v1 -->') == 1
        assert NAME in global_text
    verified = 0
    if manifest_root:
        root = Path(manifest_root).resolve()
        manifest = json.loads((root / 'SHA256_MANIFEST.json').read_text())
        assert manifest['algorithm'] == 'SHA-256' and manifest['files']
        actual = {str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}
        assert actual == set(manifest['files']) | {'SHA256_MANIFEST.json'}
        for rel, expected in manifest['files'].items():
            path = (root / rel).resolve()
            assert path.is_relative_to(root) and path.is_file() and not (root / rel).is_symlink()
            assert hashlib.sha256(path.read_bytes()).hexdigest() == expected
            verified += 1
    return {'passed': True, 'skill': str(skill), 'reference_links_verified': len(links),
            'manifest_files_verified': verified}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skill', type=Path, required=True)
    parser.add_argument('--global-file', type=Path)
    parser.add_argument('--manifest-root', type=Path)
    args = parser.parse_args()
    print(json.dumps(validate(args.skill, args.global_file, args.manifest_root), indent=2))


if __name__ == '__main__':
    main()
