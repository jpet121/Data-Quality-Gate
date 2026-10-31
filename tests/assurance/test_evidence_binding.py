import hashlib,json
from assurance.release_evidence import verify_current

def test_missing_release_evidence_never_clears_gate(tmp_path):
    errors=verify_current(tmp_path)
    assert errors
    assert any(e['id']=='source_binding' for e in errors)

def test_source_tampering_is_reported_even_if_a_run_record_claims_success(tmp_path):
    (tmp_path/'continuation_evidence').mkdir()
    source=tmp_path/'main.py';source.write_text('original')
    snapshot={'main.py':hashlib.sha256(source.read_bytes()).hexdigest()}
    (tmp_path/'continuation_evidence/final_source_snapshot.json').write_text(json.dumps(snapshot))
    source.write_text('tampered')
    errors=verify_current(tmp_path)
    assert any(e['id']=='source_binding' and 'digest_mismatch' in e['reason'] for e in errors)
