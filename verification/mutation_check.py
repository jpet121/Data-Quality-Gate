"""Bounded auditable source mutations with baseline control and real JUnit accounting."""
import ast
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
MUTATIONS=[
 ('zero_money','models.py',"gt=Decimal('0')","ge=Decimal('0')"),
 ('quantity_overflow','models.py','le=1000000','le=1000001'),
 ('duplicate_keys','parser.py','if key in seen:','if False:'),
 ('reversed_duplicate_condition','parser.py','if key in seen:','if key not in seen:'),
 ('extra_fields','core.py','if unknown:return reject','if False:return reject'),
 ('idempotency_conflict','storage.py','if current[0]!=result.input_sha256:','if False:'),
 ('batch_off_by_one','core.py','if index>=config_snapshot.max_batch:','if index>config_snapshot.max_batch:'),
 ('pg_json_dispatch','workflow.py','raw if isinstance(raw, dict) else json.loads(raw)','json.loads(raw)'),
 ('line_arithmetic','models.py','line.quantity * cents','line.quantity + cents'),
 ('null_sink','workflow.py',"if sink is None:return 'DISABLED'","if False:return 'DISABLED'"),
 ('retry_default','storage.py','max_attempts:int=3','max_attempts:int=4'),
 ('premature_commit','storage.py',"            # Explicit quarantine record", "            c.execute('COMMIT')\n            # Explicit quarantine record"),
 ('wrong_transition','storage.py',"state='DONE' if success", "state='RETRY' if success"),
 ('lost_attempt_update','storage.py','attempts=attempts+1','attempts=attempts'),
 ('lost_record_serialization','models.py','self.model_dump_json(exclude_none=True)',"self.model_dump_json(exclude_none=True,exclude={'record'})"),
 ('removed_parse_handler','core.py','except ParseFault as e:return reject(Failure.PARSE_ERROR,e.code)','except ParseFault as e:raise'),
]

def classify(exit_code: int, counts: dict | None, timed_out: bool = False) -> str:
    if timed_out:return 'timed_out'
    if not counts or counts['total']<=0:return 'harness_error'
    if counts['errors'] or counts['skipped']:return 'harness_error'
    if exit_code==1 and counts['failed']>0:return 'killed'
    if exit_code==0 and counts['failed']==0:return 'survived'
    return 'harness_error'

def run_suite(dst: Path,label: str) -> dict:
    started=datetime.now(timezone.utc).isoformat()
    result_file=dst/'mutation-results.xml'
    command=[sys.executable,'-m','pytest','-q','test_suite.py','tests',
             '--ignore=tests/integration/test_postgres_independent.py','--hypothesis-seed=20261029',
             '--junitxml='+str(result_file)]
    timeout=False
    try:
        p=subprocess.run(command,cwd=dst,capture_output=True,text=True,timeout=60,
                         env={**os.environ,'PYTHONPATH':str(dst/'src')})
        code=p.returncode;output=p.stdout+p.stderr
    except subprocess.TimeoutExpired as exc:
        timeout=True;code=124
        output=(exc.stdout or b'').decode(errors='replace') if isinstance(exc.stdout,bytes) else (exc.stdout or '')
    counts=None
    if result_file.exists():
        (ROOT/'continuation_evidence'/f'mutation_{label}.xml').write_bytes(result_file.read_bytes())
        tree=ET.parse(result_file).getroot();suites=[tree] if tree.tag=='testsuite' else list(tree)
        counts={name:sum(int(s.get(field,0)) for s in suites) for name,field in [('total','tests'),('failed','failures'),('errors','errors'),('skipped','skipped')]}
    (ROOT/'continuation_evidence'/f'mutation_{label}.txt').write_text(output)
    return {'label':label,'command':command,'exit_code':code,'timed_out':timeout,'counts':counts,
            'outcome':classify(code,counts,timeout),'started_at':started,'completed_at':datetime.now(timezone.utc).isoformat()}

def copy_target(dst: Path, source: Path = ROOT) -> None:
    ignore=shutil.ignore_patterns('__pycache__','.pytest_cache','.hypothesis','*.egg-info')
    for item in ['src','tests','assurance','verification','formal','specifications','examples','test_suite.py','verify_release.py','pyproject.toml','main.py','tools','scripts','migrations']:
        p=source/item
        if p.is_dir():shutil.copytree(p,dst/item,ignore=ignore)
        else:shutil.copy2(p,dst/item)
    (dst/'continuation_evidence').mkdir()

def main() -> int:
    (ROOT/'continuation_evidence').mkdir(exist_ok=True)
    source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'src').rglob('*.py')}
    results=[]
    snapshot=tempfile.TemporaryDirectory(prefix='sesv-mutation-frozen-')
    frozen=Path(snapshot.name)
    copy_target(frozen)
    with tempfile.TemporaryDirectory(prefix='sesv-mutation-control-') as d:
        copy_target(Path(d),frozen);control=run_suite(Path(d),'baseline')
    control_ok=control['exit_code']==0 and control['outcome']=='survived'
    if control_ok:
        for name,module,before,after in MUTATIONS:
            with tempfile.TemporaryDirectory(prefix='sesv-mutant-') as d:
                dst=Path(d);copy_target(dst,frozen);p=dst/'src/event_validator'/module
                text=p.read_text()
                if text.count(before)!=1:
                    results.append({'label':name,'outcome':'harness_error','reason':'mutation anchor not unique'});continue
                mutated=text.replace(before,after);p.write_text(mutated)
                try:ast.parse(mutated)
                except SyntaxError:
                    results.append({'label':name,'outcome':'invalid','reason':'uncompilable mutant'});continue
                r=run_suite(dst,name);r['source_module']=module
                r['mutated_source_sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
                if r['counts'] and r['counts']['total']!=control['counts']['total']:
                    r['outcome']='harness_error';r['reason']='collection differs from baseline'
                results.append(r);print(name,r['outcome'],flush=True)
    states=['killed','survived','invalid','timed_out','harness_error']
    counts={state:sum(r['outcome']==state for r in results) for state in states}
    denominator=counts['killed']+counts['survived']
    report={'schema_version':'2','baseline':control,'baseline_passed':control_ok,'generated':len(MUTATIONS),
            'executed':sum('exit_code' in r for r in results),'results':results,'counts':counts,
            'not_executed':len(MUTATIONS)-len(results),'confirmed_equivalent':0,
            'score_numerator':counts['killed'],'score_denominator':denominator,
            'excluded_from_score':['invalid','timed_out','harness_error','not_executed'],
            'baseline_source_hashes':source_hashes,'owner_approved_threshold':None,'risk_acceptance':'NOT GRANTED'}
    report['authoritative_source_unchanged']=all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==sha for p,sha in source_hashes.items())
    (ROOT/'continuation_evidence/mutation_report.json').write_text(json.dumps(report,indent=2))
    snapshot.cleanup()
    return 0 if control_ok and counts['killed']==len(MUTATIONS) and report['authoritative_source_unchanged'] else 1

if __name__=='__main__':raise SystemExit(main())
