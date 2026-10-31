import hashlib
import importlib.util
from pathlib import Path
import pytest

spec=importlib.util.spec_from_file_location('release_integrity',Path(__file__).resolve().parents[2]/'verify_release.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

@pytest.mark.parametrize('manifest',[None,[],{}, {'files':{}},{'files':[]}, {'files':{'../secret':'0'*64}},
 {'files':{'/etc/passwd':'0'*64}}, {'files':{'a/../b':'0'*64}}, {'files':{'a\\b':'0'*64}},
 {'files':{'C:secret':'0'*64}}, {'files':{'x':'not-a-digest'}}, {'files':{'SHA256_MANIFEST.json':'0'*64}}])
def test_invalid_manifests_fail_closed(tmp_path,manifest):
    assert module.verify_manifest(tmp_path,manifest)

def test_valid_file_and_tamper_detection(tmp_path):
    p=tmp_path/'main.py';p.write_bytes(b'validated')
    manifest={'files':{'main.py':hashlib.sha256(p.read_bytes()).hexdigest()}}
    assert module.verify_manifest(tmp_path,manifest)==[]
    p.write_bytes(b'tampered')
    assert module.verify_manifest(tmp_path,manifest)==['digest_mismatch:main.py']

def test_symlink_cannot_redirect_manifest_read(tmp_path):
    outside=tmp_path.parent/'outside-control';outside.write_bytes(b'outside')
    (tmp_path/'link').symlink_to(outside)
    assert module.verify_manifest(tmp_path,{'files':{'link':hashlib.sha256(b'outside').hexdigest()}})==['symlink_or_path_escape:link']

def test_duplicate_manifest_keys_rejected():
    import json
    with pytest.raises(ValueError,match='duplicate_manifest_key'):
        json.loads('{"files":{},"files":{"x":"y"}}',object_pairs_hook=module._unique)
