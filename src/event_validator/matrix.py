"""Strict data-only matrix loader: no plugins, eval, free-form regex or dynamic import."""
from __future__ import annotations
import hashlib, json
from pathlib import Path
from typing import Any, Mapping, get_args
from types import MappingProxyType
from .models import MODEL_REGISTRY, ConfigSnapshot

ALLOWED_KINDS={'str','money','integer','timestamp','lines_json'}
ALLOWED_MATCH_FIELDS={'event'}
ALLOWED_ALIASES={'event':'event_type','tenant':'tenant_id','order':'order_id'}


# Approved decode kinds are part of the immutable code-defined model contract.
# A matrix cannot silently reinterpret an integer, money, date or nested record.
DECLARED_KIND_BY_FIELD: dict[str, str] = {
    'occurred_at': 'timestamp',
    'gross_amount': 'money',
    'authorized_amount': 'money',
    'quantity': 'integer',
    'lines_json': 'lines_json',
}

def _expected_kind(field: str) -> str:
    return DECLARED_KIND_BY_FIELD.get(field, 'str')

class ConfigError(ValueError):
    pass


def _valid_unicode_scalar_string(value: str) -> bool:
    """Reject lone UTF-16 surrogates in metadata emitted in canonical JSON."""
    return not any(0xD800 <= ord(char) <= 0xDFFF for char in value)

def canonical_bytes(value:Any)->bytes:
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()



def _freeze(obj: Any) -> Any:
    if isinstance(obj,dict):return MappingProxyType({k:_freeze(v) for k,v in obj.items()})
    if isinstance(obj,list):return tuple(_freeze(v) for v in obj)
    return obj

def load_matrix(path:str|Path)->ConfigSnapshot:
    def duplicates(items: list[tuple[str, Any]]) -> dict[str, Any]:
        out={}
        for k,v in items:
            if k in out: raise ConfigError('duplicate_config_key')
            out[k]=v
        return out
    try:
        with Path(path).open('rb') as stream:
            raw=stream.read(262145)
        if len(raw)>262144: raise ConfigError('config_size_limit')
        obj=json.loads(raw,object_pairs_hook=duplicates)
        if not isinstance(obj,dict) or set(obj)!={'version','limits','aliases','events'}:raise ConfigError('config_top_level')
        if not isinstance(obj['version'],str) or not obj['version']:raise ConfigError('config_version')
        if not _valid_unicode_scalar_string(obj['version']):raise ConfigError('invalid_unicode_config')
        limits=obj['limits']
        if set(limits)!={'max_event_bytes','max_tokens','max_batch'}:raise ConfigError('config_limits')
        if any(type(limits[k]) is not int or not 0<limits[k]<=bound for k,bound in [('max_event_bytes',65536),('max_tokens',256),('max_batch',100000)]):raise ConfigError('unsafe_budget')
        aliases=obj['aliases']
        if not isinstance(aliases,dict) or any((k,v) not in ALLOWED_ALIASES.items() for k,v in aliases.items()):raise ConfigError('unauthorized_alias')
        events=obj['events']
        if not isinstance(events,list) or not 1<=len(events)<=64:raise ConfigError('event_count')
        ids=set()
        for e in events:
            if not isinstance(e,dict) or set(e)!={'event_type','schema_id','schema_version','registry_key','matcher','required','optional','field_types'}:raise ConfigError('event_shape')
            if not isinstance(e['registry_key'],str) or e['registry_key'] not in MODEL_REGISTRY:raise ConfigError('registry_key_unverified')
            if any(not isinstance(e[k],str) or not e[k] or len(e[k])>128 or
                   not _valid_unicode_scalar_string(e[k])
                   for k in ('schema_id','schema_version','event_type')):
                raise ConfigError('schema_identifier')
            if (e['schema_id'],e['schema_version']) in ids:raise ConfigError('duplicate_schema')
            ids.add((e['schema_id'],e['schema_version']))
            if not isinstance(e['event_type'],str) or not e['event_type']:raise ConfigError('event_type')
            m=e['matcher']
            if not isinstance(m,dict) or set(m)!={'field','equals','priority'} or m['field'] not in ALLOWED_MATCH_FIELDS or not isinstance(m['equals'],str) or type(m['priority']) is not int or not 0<=m['priority']<=100: raise ConfigError('unsafe_matcher')
            if not isinstance(e['required'],list) or not isinstance(e['optional'],list) or len(set(e['required']+e['optional']))!=len(e['required']+e['optional']):raise ConfigError('duplicate_fields')
            if not isinstance(e['field_types'],dict):raise ConfigError('field_types')
            if set(e['field_types'])!=set(e['required']+e['optional']) or any(v not in ALLOWED_KINDS for v in e['field_types'].values()):raise ConfigError('field_types')
            if set(e['field_types'])!=set(MODEL_REGISTRY[e['registry_key']].model_fields):raise ConfigError('registry_fields_mismatch')
            if 'event_type' not in e['required'] or e['event_type'] != m['equals']:raise ConfigError('event_matcher_mismatch')
            model = MODEL_REGISTRY[e['registry_key']]
            if e['event_type'] != get_args(model.model_fields['event_type'].annotation)[0]:
                raise ConfigError('event_registry_mismatch')
            if set(e['required']) != {name for name,field in model.model_fields.items() if field.is_required()}:
                raise ConfigError('required_fields_mismatch')
            if any(kind != _expected_kind(name) for name,kind in e['field_types'].items()):
                raise ConfigError('field_kind_mismatch')
        return ConfigSnapshot(obj['version'],hashlib.sha256(canonical_bytes(obj)).hexdigest(),tuple(_freeze(e) for e in events),limits['max_event_bytes'],limits['max_tokens'],limits['max_batch'],MappingProxyType(dict(aliases)))
    except (OSError,UnicodeError,ValueError,TypeError,KeyError,RecursionError) as exc:
        if isinstance(exc,ConfigError): raise
        raise ConfigError('matrix_not_valid') from exc
