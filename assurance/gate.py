"""Fail-closed acceptance evaluator. No power to grant human release approval."""
import json
from pathlib import Path
from typing import Any

STATES={'PASS','FAIL','INCONCLUSIVE','UNPROVEN','BLOCKED'}

def evaluate(rows: list[dict[str, Any]], tests: dict[str,int], calibration: bool,
             approvals: dict[str,bool]) -> dict[str, Any]:
    blockers=[]
    def fail(key: str, reason: str, state: str = 'FAIL') -> None:
        blockers.append({'id':key,'state':state,'reason':reason})
    if not isinstance(rows,list) or not rows:
        fail('matrix','no valid requirement baseline','BLOCKED')
        rows=[]
    seen=set()
    for row in rows:
        if not isinstance(row,dict):
            fail('matrix','requirement row is not an object'); continue
        key=row.get('id')
        if not isinstance(key,str) or not key.strip():
            fail('matrix','invalid requirement ID'); continue
        if key in seen: fail(key,'duplicate requirement ID')
        seen.add(key)
        mandatory=row.get('mandatory',True)
        if type(mandatory) is not bool: fail(key,'mandatory must be boolean')
        status=row.get('status')
        valid_status=isinstance(status,str) and status in STATES
        if not valid_status: fail(key,'invalid disposition')
        evidence=row.get('evidence')
        valid_evidence=(isinstance(evidence,list) and bool(evidence) and
                        all(isinstance(x,str) and bool(x.strip()) for x in evidence))
        if mandatory is not False and (status!='PASS' or not valid_evidence):
            fail(key,row.get('reason','unverified obligation'),status if valid_status and status!='PASS' else 'FAIL')
        if mandatory is False and (not isinstance(row.get('scope_reason'),str) or not row['scope_reason'].strip()):
            fail(key,'undocumented scope exclusion')
    if not isinstance(tests,dict):
        fail('required_tests','test counts must be an object')
    else:
        counts={k:tests.get(k,0) for k in ['passed','failed','errors','skipped']}
        if any(type(n) is not int or n<0 for n in counts.values()):
            fail('required_tests','test counts must be nonnegative integers')
        else:
            if counts['passed']<=0 or any(counts[k] for k in ['failed','errors','skipped']):
                fail('required_tests','zero tests, failures, errors or unauthorized skips')
            if 'total' in tests and (type(tests['total']) is not int or tests['total']!=sum(counts.values())):
                fail('required_tests','reported total contradicts outcome counts')
    if calibration is not True: fail('calibration','harness calibration not explicitly passed')
    for key in ['requirements_oracle','mutation_thresholds','human_release']:
        if not isinstance(approvals,dict) or approvals.get(key) is not True:
            fail(key,'required owner decision not recorded','BLOCKED')
    return {'status':'NOT APPROVED' if blockers else 'AUTOMATED_CRITERIA_MET',
            'human_approval_granted_by_evaluator':False,'blocking_obligations':blockers}

def evidence_errors(rows: list[dict[str, Any]], root: Path) -> list[dict[str, str]]:
    errors=[]
    base=root.resolve()
    for row in rows:
        if not isinstance(row,dict):
            errors.append({'id':'matrix','state':'FAIL','reason':'malformed evidence row'});continue
        if row.get('status')!='PASS': continue
        items=row.get('evidence',[])
        if not isinstance(items,list) or any(not isinstance(x,str) for x in items):
            errors.append({'id':str(row.get('id')),'state':'FAIL','reason':'malformed evidence paths'});continue
        for rel in items:
            candidate=(base/rel).resolve()
            if not candidate.is_relative_to(base) or not candidate.is_file():
                errors.append({'id':row['id'],'state':'FAIL','reason':'missing or escaping evidence path: '+str(rel)})
    return errors

if __name__=='__main__':
    root=Path(__file__).resolve().parents[1]
    matrix=json.loads((root/'REQUIREMENTS_TRACEABILITY.json').read_text())
    inputs=json.loads((root/'final_evidence/gate_inputs.json').read_text())
    result=evaluate(matrix['requirements'],**inputs)
    result['blocking_obligations'].extend(evidence_errors(matrix['requirements'],root))
    from .release_evidence import verify_current
    result['blocking_obligations'].extend(verify_current(root))
    if result['blocking_obligations']: result['status']='NOT APPROVED'
    technical=[x for x in result['blocking_obligations'] if x['id'] not in {'human_release','V:UD_RELEASE','V:P_SEC17_018','V:D_UD_RELEASE_T_STAGE9'}]
    result['technical_status']='TECHNICALLY VERIFIED' if not technical else 'UNRESOLVED'
    if not technical and result['blocking_obligations']:result['status']='APPROVAL PENDING'
    (root/'final_evidence/release_gate.json').write_text(json.dumps(result,indent=2))
    print(result['status'],len(result['blocking_obligations']),'blocking obligations')
    raise SystemExit(0 if not result['blocking_obligations'] else 2)
