"""Applicable immutability rules from the now-supplied architecture references."""
from dataclasses import FrozenInstanceError
import pytest
from pydantic import ValidationError
from event_validator import validate

@pytest.mark.parametrize('event_index',range(5))
def test_accepted_records_and_nested_values_are_immutable(cfg,valid,event_index):
    result=validate(valid[event_index],'immutability',cfg)
    assert result.status=='ACCEPTED'
    before=result.canonical()
    with pytest.raises(ValidationError):result.status='REJECTED'
    with pytest.raises(ValidationError):result.record.event_id='CHANGED'
    if getattr(result.record,'lines_json',None):
        with pytest.raises(ValidationError):result.record.lines_json[0].quantity=999
        with pytest.raises(TypeError):result.record.lines_json[0]='changed'
    assert result.canonical()==before

def test_matrix_is_deeply_immutable_and_identity_stable(cfg):
    before=cfg.fingerprint
    with pytest.raises(FrozenInstanceError):cfg.version='changed'
    with pytest.raises(TypeError):cfg.aliases['event']='changed'
    with pytest.raises(TypeError):cfg.specs[0]['schema_id']='changed'
    with pytest.raises(TypeError):cfg.specs[0]['matcher']['priority']=999
    with pytest.raises(TypeError):cfg.specs[0]['required'][0]='changed'
    assert cfg.fingerprint==before

def test_domain_and_validation_do_not_depend_on_storage_or_configuration_io():
    import ast
    from pathlib import Path
    root=Path(__file__).resolve().parents[2]/'src/event_validator'
    for name in ['models.py','parser.py','core.py','workflow.py']:
        tree=ast.parse((root/name).read_text())
        imports=[n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom) and n.level]
        assert not set(imports)&{'storage','postgres','cli','matrix'},(name,imports)

def test_config_snapshot_import_compatibility():
    from event_validator.models import ConfigSnapshot as domain
    from event_validator.matrix import ConfigSnapshot as public_legacy
    from event_validator import ConfigSnapshot as public
    assert domain is public_legacy is public
