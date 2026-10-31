"""Machine-checked idempotency model exercised against actual SQLite transactions."""
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import tempfile
from event_validator import load_matrix,validate
from event_validator.storage import SQLiteRepository,IdempotencyConflict

ROOT=Path(__file__).resolve().parents[1]

def verify() -> dict:
    lean=os.environ.get('SESV_LEAN') or shutil.which('lean')
    if not lean:raise RuntimeError('Lean checker required for idempotency proof')
    source=ROOT/'formal/Idempotency.lean'
    with tempfile.TemporaryDirectory(prefix='sesv-idempotency-proof-') as temp:
        checked=subprocess.run([lean,'-j','1','-o',str(Path(temp)/'Idempotency.olean'),str(source)],capture_output=True,text=True,timeout=30)
    (ROOT/'continuation_evidence/idempotency_checker.txt').write_text(checked.stdout+checked.stderr)
    if checked.returncode or 'sorryAx' in checked.stdout:raise RuntimeError('Idempotency proof check failed')
    rng=random.Random(20261029)
    traces=[[(0,1),(0,1),(0,2),(1,3),(1,3)]]
    traces += [[(rng.randrange(6),rng.randrange(1,6)) for _ in range(40)] for _ in range(50)]
    encoded=[';'.join(str(k)+','+str(v) for k,v in trace) for trace in traces]
    model=subprocess.run([lean,'-j','1','--run',str(source),*encoded],capture_output=True,text=True,timeout=30)
    (ROOT/'continuation_evidence/idempotency_model.txt').write_text(model.stdout+model.stderr)
    if model.returncode:raise RuntimeError('Idempotency model execution failed')
    outcomes=[line.split(';') for line in model.stdout.splitlines() if line and line[0] in 'CDX' and ':' in line]
    if len(outcomes)!=len(traces):raise RuntimeError('Missing model traces')
    cfg=load_matrix(ROOT/'examples/matrix_v1.json')
    template=json.loads((ROOT/'examples/valid.jsonl').read_text().splitlines()[1])['raw']
    comparisons=0
    def raw_payload(key: int, token: int) -> str:
        return template.replace('event_id=EVT-002','event_id=MODEL-'+str(key)).replace('authorized_amount=25.00','authorized_amount='+str(token)+'.00')
    def result(key: int, token: int):
        value=validate(raw_payload(key,token),'model-check',cfg)
        if value.status!='ACCEPTED':raise RuntimeError('Invalid model test setup')
        return value
    for trace,answers in zip(traces,outcomes):
        state={};repo=SQLiteRepository(':memory:');repo.migrate()
        try:
            if len(trace)!=len(answers):raise RuntimeError('Missing model operations')
            for (key,token),answer in zip(trace,answers):
                expected,stored=answer.split(':');value=result(key,token)
                try:
                    actual=repo.persist(value,value.record.tenant_id,value.record.event_id)
                    code={'CREATED':'C','DUPLICATE':'D'}[actual]
                except IdempotencyConflict:code='X'
                if code!=expected:raise AssertionError(('status divergence',key,token,code,expected))
                state[key]=int(stored)
                rows=repo.connection.execute('SELECT event_ref,input_hash,tenant_id,matrix_version_id FROM event_ingestion').fetchall()
                if any(tenant!='TEN-ACME' or fingerprint!=cfg.fingerprint for event,digest,tenant,fingerprint in rows):
                    raise AssertionError('delivery identity divergence')
                observed={int(event.removeprefix('MODEL-')):digest for event,digest,tenant,fingerprint in rows}
                predicted={k:hashlib.sha256(raw_payload(k,v).encode('utf-8')).hexdigest() for k,v in state.items()}
                if observed!=predicted:raise AssertionError('state divergence or partial write')
                counts=repo.counts()
                if not (counts['event_ingestion']==counts['validation_result']==counts['workflow_outbox']==len(state)):
                    raise AssertionError('atomicity/count divergence')
                comparisons+=1
        finally:repo.close()
    report={'checked_theorems':5,'traces':len(traces),'compared_operations':comparisons,'disagreements':0,
            'proof_source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'seed':20261029,'passed':True,
            'formal_scope':'opaque identity/hash equality model; equal replay and conflict preserve store, creation preserves other keys',
            'empirical_scope':'actual SQLite accepted-event persistence, full logical-key/hash state and atomic result/outbox counts after every operation',
            'assumptions':['identity embedding is injective over generated keys','cryptographic collision resistance is not proved'],
            'python_formal_equivalence':'NOT ESTABLISHED; finite correspondence only'}
    (ROOT/'continuation_evidence/idempotency_proof.json').write_text(json.dumps(report,indent=2))
    return report

if __name__=='__main__':print(json.dumps(verify(),indent=2))
