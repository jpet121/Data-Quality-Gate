"""Checked gate model plus empirical correspondence; not a proof of Python equivalence."""
import hashlib
import itertools
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from .gate import evaluate

ROOT=Path(__file__).resolve().parents[1]

def verify() -> dict:
    lean=os.environ.get('SESV_LEAN') or shutil.which('lean')
    if not lean: raise RuntimeError('Lean checker required; set SESV_LEAN to a verified Lean 4.24.0 executable')
    source=ROOT/'formal/ReleaseGate.lean'
    text=source.read_text()
    if re.search(r'\b(sorry|admit|axiom)\b',text): raise ValueError('unapproved proof gap or axiom declaration')
    version=subprocess.run([lean,'--version'],capture_output=True,text=True,check=True,timeout=10).stdout.strip()
    with tempfile.TemporaryDirectory(prefix='sesv-lean-') as temp:
        checked=subprocess.run([lean,'-j','1','-o',str(Path(temp)/'ReleaseGate.olean'),str(source)],capture_output=True,text=True,timeout=30)
    (ROOT/'continuation_evidence/lean_checker.txt').write_text(checked.stdout+checked.stderr)
    if checked.returncode:raise RuntimeError('Lean proof checking failed')
    if 'sorryAx' in checked.stdout or 'sorryAx' in checked.stderr: raise RuntimeError('unproved axiom in checker output')
    inputs=[];python_results=[]
    for flags in itertools.product([False,True],repeat=6):
        for size in range(5):
            for requirements in itertools.product([False,True],repeat=size):
                evidence,tests,calibration,oracle,mutation,human=flags
                rows=[{'id':str(i),'mandatory':True,'status':'PASS' if ok else 'FAIL','evidence':['control'] if evidence else []} for i,ok in enumerate(requirements)]
                result=evaluate(rows,{'passed':1,'failed':0 if tests else 1},calibration,{'requirements_oracle':oracle,'mutation_thresholds':mutation,'human_release':human})
                inputs.append(''.join('1' if b else '0' for b in flags+requirements))
                python_results.append(result['status']=='AUTOMATED_CRITERIA_MET')
    replay=subprocess.run([lean,'-j','1','--run',str(source),*inputs],capture_output=True,text=True,timeout=30)
    (ROOT/'continuation_evidence/lean_model_replay.txt').write_text(replay.stdout+replay.stderr)
    if replay.returncode:raise RuntimeError('Lean model execution failed')
    outputs=[line=='1' for line in replay.stdout.splitlines() if line in {'0','1'}]
    if len(outputs)!=len(inputs):raise RuntimeError('Missing Lean replay outputs')
    disagreements=[{'bits':bits,'python':py,'lean':model} for bits,py,model in zip(inputs,python_results,outputs) if py!=model]
    report={'checker_version':version,'proof_source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'python_gate_sha256':hashlib.sha256((ROOT/'assurance/gate.py').read_bytes()).hexdigest(),
            'checked_theorems':9,'proof_gaps':0,'logical_axioms':['Lean built-in propositional extensionality (propext)'],
            'empirical_cases':len(inputs),'disagreements':disagreements,'scope':'release-gate eligibility for well-formed Boolean obligations and six gate conditions',
            'not_covered':['malformed JSON/schema validation','filesystem evidence existence','business event semantics','external delivery'],
            'formal_python_equivalence':'NOT ESTABLISHED; only model properties are proved',
            'passed':not disagreements}
    (ROOT/'continuation_evidence/formal_gate.json').write_text(json.dumps(report,indent=2))
    return report

if __name__=='__main__':
    result=verify();print(json.dumps(result,indent=2));raise SystemExit(0 if result['passed'] else 1)
