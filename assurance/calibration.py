"""Bounded, executable harness controls. These prove controls, not application semantics."""
import hashlib
import json
from pathlib import Path
import resource
import subprocess
import sys
from .compare import Observation, compare

ROOT = Path(__file__).resolve().parents[1]

def limits() -> None:
    resource.setrlimit(resource.RLIMIT_AS, (256 * 1024**2, 256 * 1024**2))
    resource.setrlimit(resource.RLIMIT_CPU, (2, 2))
    resource.setrlimit(resource.RLIMIT_FSIZE, (1024**2, 1024**2))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))

def observe(mode: str, timeout: float = 2.0) -> Observation:
    try:
        p = subprocess.run([sys.executable, '-I', str(ROOT/'assurance/worker.py'),mode],
                           capture_output=True,text=True,timeout=timeout,preexec_fn=limits)
    except subprocess.TimeoutExpired:
        return Observation('TIMEOUT')
    if p.returncode:
        return Observation('EXCEPTION',p.returncode)
    try:
        obj=json.loads(p.stdout)
        return Observation(obj['kind'],obj.get('value'))
    except (ValueError,KeyError,TypeError): return Observation('HARNESS_ERROR')

def run() -> dict:
    cases=[]
    def check(name: str, expected: str, actual: str) -> None:
        cases.append({'name':name,'injected':name!='positive_control','expected':expected,'actual':actual,'passed':expected==actual})
    correct=Observation('OK',42)
    check('positive_control','VALID_AGREEMENT',compare(correct,observe('correct'),True))
    check('incorrect_output','VALID_INPUT_DIVERGENCE',compare(correct,observe('incorrect'),True))
    check('invalid_input','PERMITTED_REJECTION_AGREEMENT',compare(Observation('REJECT','invalid'),observe('invalid'),False))
    check('unexpected_exception','UNEXPECTED_CRASH',compare(correct,observe('exception'),True))
    check('timeout','TIMEOUT',compare(correct,observe('timeout',0.15),True))
    check('resource_limit','RESOURCE_LIMIT',compare(correct,observe('resource'),True))
    check('state_isolation_positive','VALID_AGREEMENT',compare(Observation('OK',0),observe('fresh_state'),True,observe('fresh_state')))
    check('injected_state_leak','NONDETERMINISM',compare(Observation('OK',0),Observation('OK',0),True,Observation('OK',1)))
    check('nondeterministic_result','NONDETERMINISM',compare(correct,Observation('OK',42),True,Observation('OK',43)))
    check('corrupted_fixture','HARNESS_FAILURE',compare(correct,observe('corrupt'),True))
    check('broken_invariant','VALID_INPUT_DIVERGENCE',compare(Observation('OK',True),Observation('OK',False),True))
    check('reference_disagreement','ORACLE_UNCERTAINTY',compare(Observation('UNCERTAIN'),correct,True))
    check('missing_oracle','ORACLE_UNCERTAINTY',compare(None,correct,True))
    # A mutant comparator is calibrated against a frozen negative control.
    bad=compare(correct,Observation('OK',43),True,comparator=lambda a,b:True)
    check('incorrect_comparator_detected','REJECTED', 'REJECTED' if bad!='VALID_INPUT_DIVERGENCE' else 'MISSED')
    negative_controls=[compare(Observation('OK',i),Observation('OK',i),True) for i in range(20)]
    return {'scope':'synthetic harness calibration only','controls':cases,'passed':all(c['passed'] for c in cases),
            'false_positives':sum(x!='VALID_AGREEMENT' for x in negative_controls),'negative_control_denominator':20,
            'budgets':{'memory_bytes_per_worker':256*1024**2,'cpu_seconds_per_worker':2,'wall_seconds_per_worker':2,'timeout_control_seconds':0.15,'workers':1},
            'comparator_source_sha256':hashlib.sha256((ROOT/'assurance/compare.py').read_bytes()).hexdigest()}

if __name__=='__main__':
    result=run()
    (ROOT/'final_evidence/calibration.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['passed'] else 1)
