"""Bounded, reproducible local differential campaign against the independent oracle."""
import argparse
from datetime import datetime,timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import random
import resource
import time
from typing import Any
from .reference import expected
from event_validator import load_matrix,validate

ROOT=Path(__file__).resolve().parents[1]


def render(fields: dict[str,str], rng: random.Random) -> str:
    pieces=list(fields.items());rng.shuffle(pieces)
    def encoded(value: str) -> str:
        if any(c.isspace() or c in '\\|"' for c in value) or rng.randrange(4)==0:
            return '"'+value.replace('\\','\\\\').replace('"','\\"').replace('|','\\|')+'"'
        return value
    return ' | '.join(key+'='+encoded(value) for key,value in pieces)


def generate(index: int, matrix: dict[str,Any], rng: random.Random) -> str:
    event=matrix['events'][index%len(matrix['events'])]
    fields={name:'ID-'+str(index) for name in event['required']}
    fields.update(event_type=event['event_type'],event_id='E-'+str(index),tenant_id='T-'+str(index%3),
                  order_id='O-'+str(index%19),source=rng.choice(['ERP','PAYMENT','WMS','CARRIER']),
                  occurred_at=rng.choice(['2024-02-29T12:00:00Z','2026-10-29T12:00:00.123456+14:00','2026-10-29T12:00:00-05:00']))
    for name,kind in event['field_types'].items():
        if kind=='money':fields[name]=str(rng.randint(1,999999))+'.'+str(rng.randrange(100)).zfill(2)
        if kind=='integer':fields[name]=str(rng.randint(1,1000000))
    if 'currency' in fields:fields['currency']='USD'
    if 'reason' in fields:fields['reason']=rng.choice(['CUSTOMER_REQUEST','FULFILLMENT_FAILURE'])
    if event['event_type']=='ORDER_CREATED' and rng.randrange(2):
        qty=rng.randint(1,5);price=rng.randint(1,100)
        # Alternate both explicitly supported lexical forms of exact JSON money.
        nested_price=price if rng.randrange(2) else str(price)+'.00'
        fields['lines_json']=json.dumps([{'sku_code':'SKU-A','quantity':qty,'unit_price':nested_price}],separators=(',',':'))
        fields['gross_amount']=str(qty*price)+'.00'
    # Construct valid relationships first. Invalid variations are deliberate,
    # independently adjudicated by the reference, not by the production result.
    variation=index%12
    if variation==1:fields.pop(rng.choice(event['required']))
    elif variation==2:fields['unexpected_field']='INVALID-VALUE-'+str(index)
    elif variation==3:fields['source']='INVALID'
    elif variation==4:fields['event_type']='UNSUPPORTED'
    elif variation==5:fields['occurred_at']='2026-02-30T12:00:00Z'
    for alias,canonical in matrix['aliases'].items():
        if canonical in fields and rng.randrange(2):fields[alias]=fields.pop(canonical)
    raw=render(fields,rng)
    if variation==6:
        first=next(iter(fields));raw+=' | '+first+'='+fields[first]
    elif variation==7:raw+=' |'
    elif variation==8:raw='\ud800'+raw
    elif variation==9:raw='🙂'*1025
    return raw


def canonical_record(value: dict[str,Any]) -> dict[str,Any]:
    # Immutable tuple storage and JSON arrays represent the same declared array.
    result=dict(value)
    if 'lines_json' in result:result['lines_json']=list(result['lines_json'])
    return result


def run(cases: int, seed: int, wall_budget: float = 120.0) -> dict[str,Any]:
    if not 1<=cases<=100000:raise ValueError('campaign_case_budget')
    matrix=json.loads((ROOT/'specifications/authorized_functional_baseline_v2/examples/matrix_v1.json').read_text())
    cfg=load_matrix(ROOT/'examples/matrix_v1.json')
    rng=random.Random(seed);started=time.monotonic();cpu=time.process_time();counts={};anomalies=[];replays=0
    attempted=executed=compared=valid=0;fingerprint=hashlib.sha256()
    for index in range(cases):
        if time.monotonic()-started>wall_budget:break
        raw=generate(index,matrix,rng);attempted+=1
        encoded=raw.encode('utf-8',errors='surrogatepass')
        fingerprint.update(len(encoded).to_bytes(8,'big'));fingerprint.update(encoded)
        reference=expected(raw,matrix)
        if reference.status=='ACCEPTED':valid+=1
        executed+=1
        try:
            result=validate(raw,'campaign/'+str(index),cfg)
            observed=result.record.model_dump(exclude_none=True) if result.record else None
            agreement=result.status==reference.status
            if agreement and observed is not None:agreement=reference.record is not None and canonical_record(observed)==canonical_record(reference.record)
            elif agreement:agreement=result.failure_category.value==reference.category
            compared+=1
            category='VALID_AGREEMENT' if reference.status=='ACCEPTED' else 'PERMITTED_REJECTION_AGREEMENT'
            if not agreement:category='DIVERGENCE'
            if index%97==0:
                replays+=1
                if validate(raw,'campaign/'+str(index),cfg).canonical()!=result.canonical():category='NONDETERMINISM'
            counts[category]=counts.get(category,0)+1
            if category in {'DIVERGENCE','NONDETERMINISM'}:
                anomalies.append({'index':index,'raw':raw,'expected':reference.status,'expected_category':reference.category,'observed':result.canonical()})
        except Exception as exc:
            counts['UNEXPECTED_CRASH']=counts.get('UNEXPECTED_CRASH',0)+1
            anomalies.append({'index':index,'raw':raw,'exception':type(exc).__name__})
    complete=attempted==cases
    return {'scope':'authorized local validator, fixed clarified matrix; no external systems',
            'seed':seed,'requested':cases,'attempted':attempted,'executed':executed,'compared':compared,
            'accepted_as_valid_by_oracle':valid,'replayed':replays,'outcomes':counts,
            'input_stream_sha256':fingerprint.hexdigest(),'anomalies':anomalies,'completed':complete,
            'wall_seconds':time.monotonic()-started,'cpu_seconds':time.process_time()-cpu,
            'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            'budgets':{'cases':cases,'wall_seconds':wall_budget,'workers':1,'max_generated_input_bytes':8192},
            'production_source_hashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'src/event_validator').glob('*.py')},
            'reference_source_sha256':hashlib.sha256((ROOT/'assurance/reference.py').read_bytes()).hexdigest(),
            'passed':complete and not anomalies}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases',type=int,default=1000);parser.add_argument('--seed',type=int,default=20261029)
    parser.add_argument('--authorized-local-target',action='store_true');args=parser.parse_args()
    if not args.authorized_local_target:parser.error('explicit authorized local target flag required')
    report=run(args.cases,args.seed)
    (ROOT/'continuation_evidence/differential_campaign.json').write_text(json.dumps(report,indent=2,default=str))
    print(json.dumps({k:v for k,v in report.items() if k!='anomalies'},indent=2))
    raise SystemExit(0 if report['passed'] else 1)
