"""Reproducible dependency-free robustness sweep (not a Hypothesis substitute)."""
from __future__ import annotations
import argparse
import json
import random
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from event_validator import load_matrix,validate


def main()->int:
    parser=argparse.ArgumentParser()
    parser.add_argument('--cases',type=int,default=50000)
    parser.add_argument('--seed',type=int,default=20261029)
    args=parser.parse_args()
    if args.cases<1 or args.cases>1000000:raise ValueError('invalid_case_count')
    randomizer=random.Random(args.seed)
    cfg=load_matrix(ROOT/'examples'/'matrix_v1.json')
    valid=[json.loads(x)['raw'] for x in (ROOT/'examples'/'valid.jsonl').read_text().splitlines()]
    alphabet='abcdefXYZ19_|=\\"\n\t\x00é中\ud800\udfff\U0001f642'
    for i in range(args.cases):
        if i%3==0:
            raw=''.join(randomizer.choices(alphabet,k=randomizer.randrange(0,220)))
        elif i%3==1:
            raw=randomizer.choice(valid)
            j=randomizer.randrange(len(raw)+1)
            raw=raw[:j]+randomizer.choice(alphabet)+raw[j:]
        else:
            raw=randomizer.choice(valid)
            fragments=raw.split(' | ')
            randomizer.shuffle(fragments)
            raw=' | '.join(fragments)
        ref=f'sweep/{i}'
        output=validate(raw,ref,cfg)
        assert output.status in ('ACCEPTED','REJECTED')
        assert output.canonical()==validate(raw,ref,cfg).canonical()
        parsed=json.loads(output.canonical())
        assert parsed['input_ref']==ref
        assert parsed['config_fingerprint']==cfg.fingerprint
        if parsed['status']=='REJECTED':assert 'record' not in parsed
    print(json.dumps({'seed':args.seed,'cases':args.cases,'result':'PASS','schema_hash':cfg.fingerprint},sort_keys=True))
    return 0

if __name__=='__main__':raise SystemExit(main())
