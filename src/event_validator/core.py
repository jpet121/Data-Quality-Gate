"""Deterministic orchestration. Output excludes wall-clock and raw sensitive values."""
from __future__ import annotations
from datetime import datetime
from decimal import Decimal, InvalidOperation
import hashlib, json, re
from typing import Iterable, Iterator, Any
from pydantic import ValidationError
from .models import ValidationResult, ErrorItem, Failure, Transform, MODEL_REGISTRY
from .models import ConfigSnapshot
from .parser import tokenize, ParseFault

MONEY=re.compile(r'^[0-9]+(?:\.[0-9]{1,2})?$')
INTEGER=re.compile(r'^[0-9]+$')
RFC3339=re.compile(r'^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,6})?(?:Z|[+-](?:(?:0\d|1[0-3]):[0-5]\d|14:00))$')
SENSITIVE={'customer_ref','payment_ref','tracking_ref'}

def digest(value:str)->str:
    # Surrogate-pass hashing gives a stable fingerprint even for malformed text.
    # The ingestion boundary rejects lone surrogates before parsing or persistence.
    return hashlib.sha256(value.encode('utf-8', errors='surrogatepass')).hexdigest()

def _unique_json(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out={}
    for key,v in pairs:
        if key in out:raise ValueError('duplicate_nested_key')
        out[key]=v
    return out

def _decode(field:str,kind:str,value:str) -> Any:
    if kind=='str':return value
    if kind=='money':
        if not MONEY.fullmatch(value): raise ValueError('money_lexeme')
        return Decimal(value)
    if kind=='integer':
        if not INTEGER.fullmatch(value):raise ValueError('integer_lexeme')
        return int(value)
    if kind=='timestamp':
        if not RFC3339.fullmatch(value):raise ValueError('rfc3339_lexeme')
        v=datetime.fromisoformat(value.replace('Z','+00:00'))
        if v.utcoffset() is None:raise ValueError('missing_timezone')
        return v
    if kind=='lines_json':
        x=json.loads(value,parse_float=lambda literal: _decode('unit_price','money',literal),parse_int=int,parse_constant=lambda _: (_ for _ in ()).throw(ValueError('invalid_numeric_constant')), object_pairs_hook=_unique_json)
        if not isinstance(x,list) or len(x)>100 or any(not isinstance(y,dict) or set(y)!={'sku_code','quantity','unit_price'} for y in x):raise ValueError('invalid_lines_shape')
        from .models import LineItem
        out=[]
        for line in x:
            if type(line['quantity']) is not int or (not isinstance(line['unit_price'],(str,Decimal)) and type(line['unit_price']) is not int):raise ValueError('invalid_lines_types')
            rawprice=line['unit_price']
            if isinstance(rawprice,str): rawprice=_decode('unit_price','money',rawprice)
            elif type(rawprice) is int: rawprice=Decimal(rawprice)
            out.append(LineItem.model_validate({**line,'unit_price':rawprice},strict=True))
        return tuple(out)
    raise ValueError('unsupported_kind')


def validate(raw:object,input_ref:str,config_snapshot:ConfigSnapshot,index:int=0)->ValidationResult:
    if not isinstance(input_ref,str):
        raise ValueError('invalid_input_ref')
    try:
        input_ref.encode('utf-8', errors='strict')
    except UnicodeEncodeError as exc:
        raise ValueError('invalid_input_ref') from exc
    sha=digest(raw if isinstance(raw,str) else repr(type(raw)))
    trace=['input_hash','config:'+config_snapshot.fingerprint[:16]]
    event_type: str | None = None
    schema_id: str | None = None
    schema_version: str | None = None
    transforms: list[Transform] = []
    def reject(cat:Failure,code:str,path:str='',rule:str='lexer') -> ValidationResult:
        return ValidationResult(input_ref=input_ref,index=index,config_fingerprint=config_snapshot.fingerprint,event_type=event_type,schema_id=schema_id,schema_version=schema_version,status='REJECTED',failure_category=cat,errors=(ErrorItem(path=path,rule_id=rule,code=code,message='Input rejected by '+rule+' rule '+code),),trace=tuple(trace+['rejected:'+cat.value]),transforms=tuple(transforms),input_sha256=sha)
    if not isinstance(raw,str):return reject(Failure.INPUT_LIMIT,'not_string',rule='ingestion')
    try:
        raw_size = len(raw.encode('utf-8', errors='strict'))
    except UnicodeEncodeError:
        return reject(Failure.INPUT_LIMIT,'invalid_unicode',rule='ingestion')
    if raw_size>config_snapshot.max_event_bytes:return reject(Failure.INPUT_LIMIT,'event_size_limit',rule='ingestion')
    try: tokens=tokenize(raw,config_snapshot.max_tokens)
    except ParseFault as e:return reject(Failure.PARSE_ERROR,e.code)
    trace.append('token_keys:'+','.join(sorted(k if k in {'event','event_type','event_id','tenant','tenant_id','order','order_id','occurred_at','source','customer_ref','gross_amount','currency','lines_json','payment_ref','authorized_amount','warehouse_ref','sku_code','quantity','shipment_ref','carrier_code','tracking_ref','reason'} else '<unknown>' for k,v in tokens)))
    pairs={}
    for key,value in tokens:
        canonical=config_snapshot.aliases.get(key,key)
        if canonical in pairs:return reject(Failure.PARSE_ERROR,'duplicate_alias',canonical,'normalization')
        pairs[canonical]=value
        if key!=canonical:
            transforms.append(Transform(path=canonical,rule_id='alias:'+config_snapshot.version,before_digest=digest(key),after_digest=digest(canonical)))
    trace.append('aliases_resolved')
    event_type=pairs.get('event_type')
    candidates=[spec for spec in config_snapshot.specs if spec['matcher']['field']=='event' and spec['matcher']['equals']==event_type]
    if not candidates:
        event_type = None  # Never echo unsupported, potentially sensitive raw values.
        return reject(Failure.UNSUPPORTED_EVENT,'no_match','event_type','classification')
    highest=max(s['matcher']['priority'] for s in candidates)
    candidates=[s for s in candidates if s['matcher']['priority']==highest]
    if len(candidates)!=1:return reject(Failure.AMBIGUOUS_EVENT,'multiple_match','event_type','classification')
    spec=candidates[0];schema_id=spec['schema_id'];schema_version=spec['schema_version']
    trace.append('schema:'+schema_id+':'+schema_version)
    unknown=set(pairs)-set(spec['field_types'])
    if unknown:return reject(Failure.SCHEMA_VIOLATION,'extra_field','<unexpected>','pydantic')
    missing=set(spec['required'])-set(pairs)
    if missing:return reject(Failure.SCHEMA_VIOLATION,'missing_field',sorted(missing)[0],'pydantic')
    decoded={}
    for key,value in pairs.items():
        try: decoded[key]=_decode(key,spec['field_types'][key],value)
        except (ValueError,OverflowError,InvalidOperation,ValidationError,TypeError,RecursionError):
            return reject(Failure.SCHEMA_VIOLATION,'lexical_type_error',key,'declared_type')
    trace.append('typed_lexical_decode')
    try:record=MODEL_REGISTRY[spec['registry_key']].model_validate(decoded,strict=True)
    except ValidationError as err:
        issue=err.errors()[0];path='.'.join(map(str,issue['loc']))
        return reject(Failure.SCHEMA_VIOLATION,str(issue['type']),path,'pydantic')
    trace.append('strict_pydantic_accept')
    return ValidationResult(input_ref=input_ref,index=index,config_fingerprint=config_snapshot.fingerprint,event_type=event_type,schema_id=schema_id,schema_version=schema_version,status='ACCEPTED',failure_category=None,record=record,transforms=tuple(transforms),trace=tuple(trace),input_sha256=sha)


def validate_many(raw_events:Iterable[object],batch_ref:str,config_snapshot:ConfigSnapshot) -> Iterator[ValidationResult]:
    for index,event in enumerate(raw_events):
        if index>=config_snapshot.max_batch:raise ValueError('batch_limit')
        yield validate(event,f'{batch_ref}/{index:08d}',config_snapshot,index)
