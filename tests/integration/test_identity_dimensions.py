"""Delivery identity must vary with both tenant and configuration snapshot."""
import json
from pathlib import Path
from event_validator import load_matrix,validate
from event_validator.storage import SQLiteRepository

ROOT=Path(__file__).resolve().parents[2]

def test_same_event_id_in_two_valid_tenants_is_not_a_collision(cfg,valid):
    a=validate(valid[1],'tenant-a',cfg)
    b=validate(valid[1].replace('tenant=TEN-ACME','tenant=TEN-OTHER'),'tenant-b',cfg)
    assert a.status==b.status=='ACCEPTED'
    repo=SQLiteRepository(':memory:');repo.migrate()
    try:
        assert repo.persist(a,a.record.tenant_id,a.record.event_id)=='CREATED'
        assert repo.persist(b,b.record.tenant_id,b.record.event_id)=='CREATED'
        assert repo.counts()['event_ingestion']==2
    finally:repo.close()

def test_same_tenant_event_under_distinct_snapshots_is_distinct(tmp_path,cfg,valid):
    data=json.loads((ROOT/'examples/matrix_v1.json').read_text());data['version']='isolated-test-version'
    path=tmp_path/'matrix.json';path.write_text(json.dumps(data));other=load_matrix(path)
    a=validate(valid[1],'snapshot-a',cfg);b=validate(valid[1],'snapshot-b',other)
    assert a.config_fingerprint!=b.config_fingerprint
    repo=SQLiteRepository(':memory:');repo.migrate()
    try:
        assert repo.persist(a,a.record.tenant_id,a.record.event_id)=='CREATED'
        assert repo.persist(b,b.record.tenant_id,b.record.event_id)=='CREATED'
        assert repo.persist(a,a.record.tenant_id,a.record.event_id)=='DUPLICATE'
        assert repo.counts()['event_ingestion']==2
    finally:repo.close()
