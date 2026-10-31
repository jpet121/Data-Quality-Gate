"""Bind the release decision to current source, complete test inventory and real results."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from verify_release import verify_manifest


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_current(root: Path) -> list[dict[str,str]]:
    errors=[]
    def fail(key,reason):errors.append({'id':key,'state':'FAIL','reason':reason})
    def load(rel):
        try:return json.loads((root/rel).read_text())
        except (OSError,ValueError):fail(rel,'missing or corrupt evidence');return None
    snapshot=load('continuation_evidence/final_source_snapshot.json')
    run=load('continuation_evidence/final_test_run.json')
    inventory=load('continuation_evidence/final_collection.json')
    if not isinstance(snapshot,dict) or not snapshot:
        fail('source_binding','missing source snapshot')
    else:
        for error in verify_manifest(root,{'files':snapshot}):fail('source_binding',error)
    if isinstance(run,dict):
        for key,rel in [('source_snapshot_sha256','continuation_evidence/final_source_snapshot.json'),('collection_sha256','continuation_evidence/final_collection.json'),('junit_sha256','continuation_evidence/final_suite.xml')]:
            if not (root/rel).is_file() or run.get(key)!=digest(root/rel):fail('test_binding','missing/stale '+key)
        if type(run.get('exit_code')) is not int or run.get('exit_code')!=0:fail('required_tests','complete required suite did not succeed')
    else:fail('test_binding','missing actual test-run record')
    if isinstance(inventory,dict):
        try:
            tree=ET.parse(root/'continuation_evidence/final_suite.xml')
            observed=Counter((c.get('classname'),c.get('name')) for c in tree.getroot().iter('testcase'))
            selected=Counter(tuple(item) for item in inventory['junit_identities'])
            if not selected or observed!=selected:fail('test_inventory','JUnit cases do not match the complete collected suite')
            for case in tree.getroot().iter('testcase'):
                if any(case.find(tag)is not None for tag in ['failure','error','skipped']):fail('required_tests','nonpassing required case '+str(case.get('name')))
        except (OSError,ET.ParseError,TypeError,KeyError):fail('test_inventory','unreadable test inventory or JUnit')
    else:fail('test_inventory','missing collected suite')
    mutations=load('continuation_evidence/mutation_report.json')
    policy=load('specifications/OWNER_ACCEPTANCE_DECISIONS.json')
    if (isinstance(mutations,dict) and isinstance(mutations.get('counts'),dict) and isinstance(mutations.get('baseline_source_hashes'),dict) and isinstance(policy,dict) and isinstance(policy.get('mutation_policy'),dict) and type(policy['mutation_policy'].get('selected_mutants')) is int):
        wanted=policy['mutation_policy']['selected_mutants']
        if not (mutations.get('baseline_passed') is True and mutations.get('generated')==mutations.get('executed')==wanted and mutations.get('counts',{}).get('killed')==wanted and mutations.get('authoritative_source_unchanged')is True):
            fail('mutation_policy','baseline, execution or kill count does not meet owner-approved criteria')
        if any(mutations.get('counts',{}).get(k,0) for k in ['survived','invalid','timed_out','harness_error']) or mutations.get('not_executed',0):fail('mutation_policy','unresolved mutation outcome')
        if mutations.get('baseline_source_hashes'):
            for error in verify_manifest(root,{'files':mutations['baseline_source_hashes']}):fail('mutation_binding',error)
        if not mutations.get('baseline_source_hashes'):fail('mutation_binding','no mutation source identity')
    else:fail('mutation_policy','missing mutation measurements or approved policy')
    checks=[('continuation_evidence/formal_gate.json','formal/ReleaseGate.lean',9),('continuation_evidence/idempotency_proof.json','formal/Idempotency.lean',5)]
    for rel,proof,count in checks:
        result=load(rel)
        if not isinstance(result,dict) or result.get('passed')is not True or result.get('checked_theorems')!=count or result.get('proof_source_sha256')!=digest(root/proof):
            fail('formal_binding','proof evidence missing, failed or stale: '+proof)
    formal=load('continuation_evidence/formal_gate.json')
    if isinstance(formal,dict) and formal.get('python_gate_sha256')!=digest(root/'assurance/gate.py'):fail('formal_binding','gate proof correspondence predates Python gate')
    campaign=load('continuation_evidence/differential_campaign.json')
    if not isinstance(campaign,dict) or campaign.get('passed')is not True or campaign.get('anomalies') or not (campaign.get('requested')==campaign.get('attempted')==campaign.get('executed')==campaign.get('compared')):
        fail('differential','incomplete or divergent differential campaign')
    elif campaign.get('reference_source_sha256')!=digest(root/'assurance/reference.py'):fail('differential_binding','reference model changed after campaign')
    else:
        sources=campaign.get('production_source_hashes',{})
        if not sources:fail('differential_binding','missing production identity')
        if sources:
            for error in verify_manifest(root,{'files':sources}):fail('differential_binding',error)
    return errors
