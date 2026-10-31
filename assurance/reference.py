"""Independent regex/stdlib oracle from the owner-designated functional documents.

No production imports or Pydantic dependency. Detailed production error text and
hash implementation are deliberately not used as correctness criteria.
"""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from fractions import Fraction
import json
from pathlib import Path
import re
from typing import Any

FIELD=re.compile(r'\s*([A-Za-z0-9_]+)\s*=\s*(?:"((?:[^"\\]|\\["\\|])*)"|([^\s|"\\]+))\s*(?=\||$)')
IDENTIFIER=re.compile(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}')
CASH=re.compile(r'[0-9]+(?:\.[0-9]{1,2})?')
COUNT=re.compile(r'[0-9]+')
DATE=re.compile(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,6})?(?:Z|[+-](?:(?:0[0-9]|1[0-3]):[0-5][0-9]|14:00))')

@dataclass(frozen=True)
class Expected:
    status: str
    category: str | None = None
    record: dict[str,Any] | None = None

class Reject(ValueError):
    def __init__(self,category: str):self.category=category


def lex(text: str, budget: int) -> dict[str,str]:
    fields={};position=0
    while position<len(text):
        match=FIELD.match(text,position)
        if not match:raise Reject('PARSE_ERROR')
        key=match[1]
        if key in fields:raise Reject('PARSE_ERROR')
        if match[2] is None:value=match[3]
        else:
            value=re.sub(r'\\(["\\|])',lambda m:m[1],match[2])
        if not value:raise Reject('PARSE_ERROR')
        fields[key]=value
        if len(fields)>budget:raise Reject('PARSE_ERROR')
        position=match.end()
        if position==len(text):return fields
        position+=1
        if position==len(text) or not text[position:].strip():raise Reject('PARSE_ERROR')
    raise Reject('PARSE_ERROR')


def money(value: str) -> Decimal:
    if not CASH.fullmatch(value):raise Reject('SCHEMA_VIOLATION')
    amount=Decimal(value)
    if amount<=0:raise Reject('SCHEMA_VIOLATION')
    # Owner-delegated reconciliation retained and documented this strict profile.
    if amount>Decimal('9999999999999.99'):raise Reject('SCHEMA_VIOLATION')
    return amount


def unique(pairs: list[tuple[str,Any]]) -> dict[str,Any]:
    result={}
    for key,value in pairs:
        if key in result:raise Reject('SCHEMA_VIOLATION')
        result[key]=value
    return result


def expected(raw: object, matrix: dict[str,Any]) -> Expected:
    try:
        if not isinstance(raw,str):raise Reject('INPUT_LIMIT')
        try:size=len(raw.encode('utf-8'))
        except UnicodeError:raise Reject('INPUT_LIMIT')
        if size>matrix['limits']['max_event_bytes']:raise Reject('INPUT_LIMIT')
        supplied=lex(raw,matrix['limits']['max_tokens']);fields={}
        for key,value in supplied.items():
            name=matrix['aliases'].get(key,key)
            if name in fields:raise Reject('PARSE_ERROR')
            fields[name]=value
        matches=[entry for entry in matrix['events'] if entry['matcher']['equals']==fields.get('event_type')]
        if not matches:raise Reject('UNSUPPORTED_EVENT')
        priority=max(entry['matcher']['priority'] for entry in matches)
        winners=[entry for entry in matches if entry['matcher']['priority']==priority]
        if len(winners)!=1:raise Reject('AMBIGUOUS_EVENT')
        schema=winners[0]
        if not set(schema['required'])<=fields.keys() or not fields.keys()<=schema['field_types'].keys():raise Reject('SCHEMA_VIOLATION')
        decoded={}
        for key,value in fields.items():
            kind=schema['field_types'][key]
            if kind=='str':decoded[key]=value
            elif kind=='integer':
                if not COUNT.fullmatch(value):raise Reject('SCHEMA_VIOLATION')
                decoded[key]=int(value)
                if not 1<=decoded[key]<=1000000:raise Reject('SCHEMA_VIOLATION')
            elif kind=='money':decoded[key]=money(value)
            elif kind=='timestamp':
                if not DATE.fullmatch(value):raise Reject('SCHEMA_VIOLATION')
                decoded[key]=datetime.fromisoformat(value.replace('Z','+00:00'))
            elif kind=='lines_json':
                lines=json.loads(value,parse_float=money,parse_int=int,object_pairs_hook=unique,
                                 parse_constant=lambda value:(_ for _ in ()).throw(Reject('SCHEMA_VIOLATION')))
                if not isinstance(lines,list) or len(lines)>100:raise Reject('SCHEMA_VIOLATION')
                decoded[key]=[]
                for line in lines:
                    if not isinstance(line,dict) or set(line)!={'sku_code','quantity','unit_price'}:raise Reject('SCHEMA_VIOLATION')
                    if type(line['quantity'])is not int or not 1<=line['quantity']<=1000000:raise Reject('SCHEMA_VIOLATION')
                    if not isinstance(line['sku_code'],str) or not IDENTIFIER.fullmatch(line['sku_code']):raise Reject('SCHEMA_VIOLATION')
                    price=line['unit_price']
                    if isinstance(price,str):price=money(price)
                    elif type(price)is int:price=money(str(price))
                    elif not isinstance(price,Decimal):raise Reject('SCHEMA_VIOLATION')
                    if price<=0:raise Reject('SCHEMA_VIOLATION')
                    decoded[key].append({**line,'unit_price':price})
        identifiers=set(fields)-{'event_type','source','occurred_at','currency','reason','quantity','gross_amount','authorized_amount','lines_json'}
        if any(not IDENTIFIER.fullmatch(decoded[name]) for name in identifiers):raise Reject('SCHEMA_VIOLATION')
        if decoded['source'] not in {'ERP','PAYMENT','WMS','CARRIER'}:raise Reject('SCHEMA_VIOLATION')
        if 'currency' in decoded and decoded['currency']!='USD':raise Reject('SCHEMA_VIOLATION')
        if 'reason' in decoded and decoded['reason'] not in {'CUSTOMER_REQUEST','FULFILLMENT_FAILURE'}:raise Reject('SCHEMA_VIOLATION')
        if 'lines_json' in decoded:
            total=sum((line['quantity']*Fraction(line['unit_price']) for line in decoded['lines_json']),Fraction(0))
            if total!=Fraction(decoded['gross_amount']):raise Reject('SCHEMA_VIOLATION')
        return Expected('ACCEPTED',record=decoded)
    except Reject as exc:return Expected('REJECTED',exc.category)
    except (ValueError,TypeError,OverflowError):return Expected('REJECTED','SCHEMA_VIOLATION')
