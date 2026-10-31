"""Verify release-file SHA-256 values without trusting manifest paths or structure."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any

ROOT=Path(__file__).resolve().parent

def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result={}
    for key,value in pairs:
        if key in result:raise ValueError('duplicate_manifest_key')
        result[key]=value
    return result

def verify_manifest(root: Path, manifest: object) -> list[str]:
    if not isinstance(manifest,dict) or not isinstance(manifest.get('files'),dict) or not manifest['files']:
        return ['invalid_or_empty_manifest']
    if manifest.get('algorithm','SHA-256')!='SHA-256':return ['unsupported_digest_algorithm']
    base=root.resolve();errors=[]
    for rel,expected in manifest['files'].items():
        if (not isinstance(rel,str) or not rel or '\\' in rel or ':' in rel or
            PurePosixPath(rel).is_absolute() or any(p in {'','..','.'} for p in rel.split('/')) or
            rel=='SHA256_MANIFEST.json'):
            errors.append('unsafe_manifest_path');continue
        if not isinstance(expected,str) or not re.fullmatch('[a-f0-9]{64}',expected):
            errors.append('invalid_digest:'+rel);continue
        path=base/rel
        if not path.resolve().is_relative_to(base) or any(p.is_symlink() for p in [path,*path.parents] if p!=base and p.is_relative_to(base)):
            errors.append('symlink_or_path_escape:'+rel);continue
        try:
            digest=hashlib.sha256()
            with path.open('rb') as fh:
                for chunk in iter(lambda:fh.read(1024*1024),b''):digest.update(chunk)
            if digest.hexdigest()!=expected:errors.append('digest_mismatch:'+rel)
        except OSError:errors.append('missing_or_unreadable:'+rel)
    return errors

def main() -> int:
    try:
        with (ROOT/'SHA256_MANIFEST.json').open('rb') as fh:raw=fh.read(10*1024*1024+1)
        if len(raw)>10*1024*1024:raise ValueError('manifest_size_limit')
        manifest=json.loads(raw,object_pairs_hook=_unique)
        errors=verify_manifest(ROOT,manifest)
    except (OSError,ValueError,UnicodeError):
        print('FAILED: manifest_missing_or_invalid');return 1
    if errors:
        print('FAILED: '+','.join(errors));return 1
    print(f"PASS: {len(manifest['files'])} files match SHA-256 manifest");return 0

if __name__=='__main__':raise SystemExit(main())
