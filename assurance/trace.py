"""Lossless two-authority clause inventory and conservative evidence dispositions."""
import csv
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]

def build() -> dict:
    rows=[];inventory=[]
    override_path=ROOT/'assurance/trace_overrides.json'
    overrides=json.loads(override_path.read_text()) if override_path.exists() else {}
    documents=[('D','Development & Software Architecture.xml'),('V','COMPILE_V4_Independent_Verification_Contract.xml')]
    def disposition(authority: str, section: str, obj: dict, row_id: str) -> tuple:
        rid=obj.get('id','');mod=obj.get('modality','REQUIRED')
        revision=overrides.get(authority+':'+row_id) or overrides.get(authority+':'+rid)
        if revision:
            return (revision['status'],revision['reason'],revision['evidence'],revision.get('mandatory',True),revision.get('scope_reason',''))
        if mod in {'INFORMATIONAL','PERMITTED','PREFERRED'}:
            return ('INCONCLUSIVE','non-mandatory modality retained for audit',[],False,'XML explicitly labels this clause '+mod)
        if section in {'Branches','Dependencies','UserDecisions','IterationControls'}:
            return ('BLOCKED','Control/dependency recorded; prerequisites or reserved decisions are not all satisfied',['FINAL_EVIDENCE_REPORT.md'],True,'')
        if authority=='D':
            if rid in {'p_01','p_02','p_03','o_contract','t_publish','p_32','p_33','p_34','p_35','p_37'}:
                return ('INCONCLUSIVE','Compiler/success-only publication constraint; not a compiler execution or successful production publication',[],False,'Current user requests an audit ZIP, matrix and report, rather than contract compilation or raw-code-only success publication; no successful production release is claimed')
            verified={
             'p_12':('Structural separation and explicit workflow repository protocol inspected; no claim of full book compliance',['src/event_validator/workflow.py','final_evidence/mypy.txt']),
             'p_14':('Actual Python 3.12 runtime and 3.12 AST parsing passed',['final_evidence/full_suite.xml','tests/assurance/test_development_contract.py']),
             'p_15':('Actual Pydantic v2 execution and serialization checks passed',['final_evidence/full_suite.xml','final_evidence/dependencies.txt']),
             'p_16':('All application callable signatures annotated; mypy passes all nine modules; dynamic JSON and optional driver boundaries explicitly Any',['final_evidence/annotation_audit.json','final_evidence/mypy.txt']),
             'p_18':('Runtime dependencies limited to Pydantic; optional psycopg adapter; new audit tools do not become application runtime dependencies',['pyproject.toml']),
             'p_22':('Supported imports/dependencies and generated standalone exercised in Python 3.12',['final_evidence/full_suite.xml','final_evidence/distribution.txt']),
             'p_23':('Existing demo is executable and testable; this does not establish missing business specification completeness',['final_evidence/full_suite.xml','final_evidence/distribution.txt']),
             'p_27':('Structural, type, dependency, logic and demo-stub gaps inspected and recorded',['FINAL_EVIDENCE_REPORT.md','final_evidence/mypy_initial.txt','final_evidence/mypy.txt']),
             'p_28':('Current claims distinguish actual execution, historical evidence and unavailable checks',['FINAL_EVIDENCE_REPORT.md']),
             'p_30':('Missing inputs, scope mismatch, proof gaps and absent owner decisions explicitly recorded',['FINAL_EVIDENCE_REPORT.md']),
             'p_31':('No production readiness claimed; candidate is NOT APPROVED',['RELEASE_STATUS.json']),
             'p_38':('Blocked branch respected; package is an audit candidate, not a successful complete production implementation',['RELEASE_STATUS.json']),
             'e5':('Runtime, syntax, actual Pydantic v2 and imports executed',['final_evidence/full_suite.xml','final_evidence/distribution.txt']),
             'e6':('No unexecuted tests represented as passing',['FINAL_EVIDENCE_REPORT.md']),
             't_verify':('Available constraints audited; completeness remains blocked and is not claimed',['REQUIREMENTS_TRACEABILITY.json','FINAL_EVIDENCE_REPORT.md'])}
            if rid=='t_verify': return ('INCONCLUSIVE','Compatibility and type checks completed, but functional completeness and book fidelity remain blocked',['FINAL_EVIDENCE_REPORT.md'],True,'')
            if rid in verified:
                why,ev=verified[rid];return ('PASS',why,ev,True,'')
            if rid=='p_20':return ('FAIL','Application explicitly contains LocalStubSink and lacks production delivery/recovery implementation; do not invent an external connector to hide this development-contract mismatch',['src/event_validator/workflow.py','README.md'],True,'')
            if rid in {'p_10','p_11','p_17','p_25','e2','e4','t_arch'}:
                return ('BLOCKED','Five full original architecture books are absent; supplied development compiler package explicitly contains orientation excerpts only',['final_evidence/reference_integrity.json','FINAL_EVIDENCE_REPORT.md'],True,'')
            return ('BLOCKED','Development contract depends on separately supplied application-specific source XML; it is not included in any uploaded package. Functional completeness and preservation cannot be certified',['specifications/Development & Software Architecture.xml','FINAL_EVIDENCE_REPORT.md'],True,'')
        # Verification-only obligations: do not turn these into application business rules.
        if rid in {'P_CORE15','P_SEC23_001','P_SEC23_002','P_SEC23_003','P_SEC23_004','P_SEC23_005','P_SEC23_006','P_SEC23_007','P_SEC23_008','P_SEC23_009','P_SEC23_010','P_SEC23_011','P_SEC23_012','P_SEC23_013','P_SEC23_014','P_SEC23_015','P_SEC23_016','P_SEC23_017','P_SEC23_018','P_SEC23_019','P_SEC23_020','O_XML','O_BRIEF'}:
            return ('INCONCLUSIVE','Compiler-stage obligation, not an application audit action',[],False,'User requests downstream verification, not regeneration/certification of compiler output')
        if rid=='P_COND2' or rid=='P_REPAIR_NO_FUTURE_CERT':
            return ('INCONCLUSIVE','Application-absent contingency is inactive',[],False,'An actual application was supplied; synthetic controls are separately labeled')
        # Specific complete checks, each linked to executed or inspected evidence.
        specific={
         'P_SEC04_001':('Both XML documents frozen before new tests',['specifications/FROZEN_BASELINE.json']),
         'P_SEC04_003':('Namespaced source IDs retained',['REQUIREMENTS_TRACEABILITY.json']),
         'P_SEC04_004':('XML XPath, source-byte span, clause hash and original anchors retained',['REQUIREMENTS_TRACEABILITY.json']),
         'P_SEC04_018':('Machine-readable and human-readable traceability matrices produced',['REQUIREMENTS_TRACEABILITY.json','REQUIREMENTS_TRACEABILITY.csv']),
         'P_SEC08_001':('Actual Python 3.12/pytest/Hypothesis run',['final_evidence/full_suite.xml','final_evidence/dependencies.txt']),
         'P_SEC10_001':('Auditable bounded seven-mutant source experiment executed',['verification/mutation_check.py','final_evidence/mutation_results.json']),
         'P_SEC10_003':('Temporary copies with subprocess wall timeout; mutation source unchanged',['verification/mutation_check.py','final_evidence/mutation_results.json']),
         'P_SEC10_017':('Mutants run in disposable copies',['verification/mutation_check.py']),
         'P_SEC10_027':('Observed killed/executed denominator is 7/7; not an approved acceptance threshold',['final_evidence/mutation_summary.json']),
         'P_SEC11_001':('New comparator and gate calibration passed; scope is explicitly synthetic',['final_evidence/calibration.json','final_evidence/calibration_tests.xml']),
         'P_SEC17_001':('Explicit fail-closed release evaluator executed and refusal/positive controls tested',['assurance/gate.py','final_evidence/release_gate.json','final_evidence/calibration_tests.xml']),
         'P_SEC17_011':('Calibration controls executed successfully',['final_evidence/calibration.json','final_evidence/calibration_tests.xml']),
         'P_SEC15_001':('A and B executable profiles run separately; C explicitly blocked pending authorized budgets',['assurance/run.py','final_evidence/profile_A.json','final_evidence/profile_B.json','final_evidence/profile_C_blocked.txt']),
         'P_SEC20_016':('One-command A/B profiles provided and executed; sustained C remains blocked',['assurance/run.py','ASSURANCE_OPERATOR_GUIDE.md']),
         'P_REPAIR_PROFILE_A_1':('Rapid checks executed; PostgreSQL outside A scope, required in B',['final_evidence/profile_A.json']),
         'P_REPAIR_PROFILE_A_2':('A profile command executed successfully',['final_evidence/profile_A.json']),
         'P_REPAIR_PROFILE_B_1':('Comprehensive tests, mutations, fault injection, sweep executed',['final_evidence/profile_B.json']),
         'P_REPAIR_PROFILE_B_2':('B profile available as pre-release diagnostic, not approval',['final_evidence/profile_B.json']),
         'EV_PROFILE_1':('Distinct A profile results recorded',['final_evidence/profile_A.json']),
         'EV_PROFILE_2':('Distinct B profile results recorded',['final_evidence/profile_B.json']),
         'P_COND3':('Specification-dependent obligations remain blocked',['FINAL_EVIDENCE_REPORT.md']),
         'P_COND4':('Required formal obligations UNPROVEN; no fabricated Lean artifacts',['final_evidence/formal_obligations.json']),
         'P_COND6':('Mutation measurements reported; no owner-approved threshold fabricated',['final_evidence/mutation_summary.json','final_evidence/release_gate.json']),
         'P_SEC17_020':('Owner mutation criteria absent; release withheld',['final_evidence/release_gate.json']),
         'P_SEC02_010':('Affected acceptance obligations blocked, not inferred from code',['REQUIREMENTS_TRACEABILITY.json']),
         'P_SEC03_006':('Shared dependencies and independence limitations recorded',['ORACLE_AND_SOURCE_ASSESSMENT.md']),
         'P_SEC03_007':('No business-oracle independence or formal-equivalence claim',['ORACLE_AND_SOURCE_ASSESSMENT.md']),
         'P_SEC06_012':('Oracle confidence and common dependencies explicitly assessed',['ORACLE_AND_SOURCE_ASSESSMENT.md']),
        }
        if rid in specific:
            why,ev=specific[rid];return ('PASS',why,ev,True,'')
        if rid.startswith('EV_SOURCE_') or rid in {'P_REF1','P_REF2','P_REF3','P_REF4','P_REF5','P_REF6'} or rid.startswith('P_SEC01_00'):
            if mod=='PROHIBITED': return ('PASS','No unrelated technique or external scientific certification claimed',['ORACLE_AND_SOURCE_ASSESSMENT.md'],True,'')
            return ('INCONCLUSIVE','Six supplied files ingested and hashes verified; relevant passages reviewed. Full application-specific applicability cannot be established without source XML. Supplied Lean file is an 11-page paper, not a complete current reference manual',['final_evidence/reference_integrity.json','ORACLE_AND_SOURCE_ASSESSMENT.md'],True,'')
        if rid.startswith('P_SEC07_') or rid in {'EV_08','O_LEAN','P_SEC17_014'}:
            if mod=='PROHIBITED' or rid in {'P_SEC07_014','P_SEC07_015','P_SEC07_016','P_SEC07_017','P_SEC07_018','P_SEC07_021'}:
                return ('PASS','Proof status taxonomy recorded honestly; no machine-checked proof or Python equivalence asserted',['final_evidence/formal_obligations.json'],True,'')
            return ('UNPROVEN','No authorized application-derived proof obligations/model or Lean checker available; no proof clearance',['final_evidence/formal_obligations.json'],True,'')
        if rid.startswith('P_SEC11_'):
            return ('PASS','Applicable listed defect calibration/control executed; original application semantics are not inferred from controls',['final_evidence/calibration.json','final_evidence/calibration_tests.xml'],True,'')
        if rid.startswith('P_RELEASE_STATE') or rid in {'P_SEC17_002','P_SEC17_003','P_SEC17_004','P_SEC17_005','P_SEC17_006'}:
            return ('PASS','Gate implements all five obligation states and tests fail-closed behavior',['assurance/gate.py','final_evidence/calibration_tests.xml'],True,'')
        if rid.startswith('P_SEC09_'):
            return ('INCONCLUSIVE','Comparator taxonomy and controls implemented, but no full authoritative business oracle exists; supplied differential lexer covers only restricted unquoted subset',['assurance/compare.py','final_evidence/calibration.json','ORACLE_AND_SOURCE_ASSESSMENT.md'],True,'')
        if rid.startswith('P_SEC10_') or rid in {'EV_06','P_SEC17_013'}:
            return ('INCONCLUSIVE','Seven selected source mutants executed and killed; wider applicability and owner-approved risk criteria absent. Not all listed mutation classes exercised',['final_evidence/mutation_summary.json'],True,'')
        if rid.startswith('P_SEC18_'):
            if rid in {'P_SEC18_001','P_SEC18_002','P_SEC18_003','P_SEC18_014'} or mod=='PROHIBITED':
                return ('PASS','Disposable local targets, isolated database and synthetic controls; no production credentials or external adversarial target',['ASSURANCE_OPERATOR_GUIDE.md','final_evidence/calibration.json'],True,'')
            return ('INCONCLUSIVE','Worker CPU/memory/wall/file bounds and suite timeouts measured; full campaign-wide filesystem/network/recursion/resource enforcement not implemented',['assurance/run.py','assurance/calibration.py'],True,'')
        if rid.startswith('P_SEC08_') or rid=='EV_04':
            return ('INCONCLUSIVE','Actual bounded properties/state machines and replay statistics recorded; some listed techniques and full application domains lack independent requirement-derived obligations',['final_evidence/full_suite.txt'],True,'')
        if rid in {'P_SEC17_007','P_SEC17_008','P_SEC17_012','P_SEC17_018','P_REPAIR_ARCH1','P_REPAIR_ARCH2','P_REPAIR_ARCH3','P_REPAIR_ARCH5','EV_01','EV_02','UD_REQUIREMENTS','UD_THRESHOLDS','UD_RELEASE'}:
            return ('BLOCKED','Missing functional source/approved oracle, risk decisions, or required external approval',['FINAL_EVIDENCE_REPORT.md'],True,'')
        if mod=='PROHIBITED' or rid in {'P_CORE1','P_CORE2','P_CORE3','P_CORE4','P_CORE5','P_CORE8','P_CORE9','P_CORE13','P_CORE16','P_SEC01_011','P_SEC02_009','P_SEC06_003','P_SEC06_013','P_SEC17_019','P_SEC17_021','P_SEC17_022','P_SEC17_023','P_SEC20_021','P_SEC21_006'}:
            return ('PASS','Authority and claim restriction observed in this audit; unavailable checks never count as passing',['FINAL_EVIDENCE_REPORT.md','ORACLE_AND_SOURCE_ASSESSMENT.md'],True,'')
        return ('INCONCLUSIVE','Evidence is partial or applicability/acceptance cannot be completed from supplied inputs; no blanket compliance claim',['FINAL_EVIDENCE_REPORT.md'],True,'')

    for authority,name in documents:
        path=ROOT/'specifications'/name;raw=path.read_bytes();doc=ET.fromstring(raw)
        nodes=list(re.finditer(rb'<Node>(.*?)</Node>',raw,re.DOTALL));position=0
        for section in doc:
            if section.tag=='Objective':
                inventory.append({'authority':authority,'section':'Objective','text':section.text});continue
            for index,node in enumerate(section,1):
                obj=json.loads(node.text);match=nodes[position];position+=1
                loc={'file':'specifications/'+name,'xpath':f'/PFContract/{section.tag}/Node[{index}]','byte_start':match.start(),'byte_end':match.end(),'xml_clause_sha256':hashlib.sha256(match.group()).hexdigest()}
                inventory.append({'authority':authority,'source':loc,'record':obj})
                if section.tag in {'Entities','Provenance','ResultPolicy','CandidateSets'}:continue
                items=[(obj.get('id',f'{section.tag}-{index}'),obj)]
                if section.tag=='Outputs':
                    items=[(obj['id']+f'.{j}',{**obj,'output_parent_id':obj['id'],'requirement':text}) for j,text in enumerate(obj.get('requirements',[]),1)]
                for rid,item in items:
                    state,reason,evidence,mandatory,scope=disposition(authority,section.tag,item,rid)
                    text=item.get('requirement') or item.get('object',{}).get('value') or item.get('label') or item.get('condition') or json.dumps(item,ensure_ascii=False)
                    rows.append({'id':authority+':'+rid,'source_id':rid,'authority':'development' if authority=='D' else 'verification','section':section.tag,'modality':item.get('modality','REQUIRED'),'mandatory':mandatory,'source':loc,'source_anchors':item.get('source_anchors',[]),'expected_behavior':text,'valid_input_domain':'Owner-designated README, ACCEPTANCE and versioned example matrix; explicit clarified input profile' if authority=='D' else 'Verification artifacts and outcomes within this clause scope','invalid_input_domain':'Malformed or out-of-contract events/configuration; no additional business rules inferred' if authority=='D' else 'Missing, contradictory, failed or unproved evidence as applicable','preconditions':'Required source documents, applicable scope and authorized acceptance criteria','postconditions':text,'invariants':'Preserve development authority; no invented business rules; evidence must match executed artifact','required_error_behavior':'BLOCKED/INCONCLUSIVE/UNPROVEN/FAIL rather than unsupported PASS','interfaces':'main.py and package APIs' if authority=='D' else 'Verification/evidence interface named by clause','verification_method':'Clause review plus cited executed evidence; missing evidence is not a passing test','oracle_basis':loc,'risk':'Not owner-classified; mandatory unmet clause blocks acceptance','acceptance_criteria':text,'unresolved_assumptions':[] if state=='PASS' else [reason],'status':state,'reason':reason,'evidence':evidence,'scope_reason':scope})
        assert position==len(nodes)
    from .functional_trace import rows as functional_rows
    rows.extend(functional_rows())
    result={'schema_version':'1.0','scope':'Complete clause inventory of the TWO user-designated XML authorities; supplemental assembler is context, not replacement application requirements','requirements':rows,'source_inventory':inventory}
    (ROOT/'REQUIREMENTS_TRACEABILITY.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    with (ROOT/'REQUIREMENTS_TRACEABILITY.csv').open('w',newline='') as f:
        fields=['id','authority','section','modality','mandatory','expected_behavior','status','reason','evidence','scope_reason','source']
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        for row in rows:writer.writerow({k:json.dumps(row[k],ensure_ascii=False) if isinstance(row[k],(list,dict)) else row[k] for k in fields})
    lines=['# Requirements traceability matrix','','Every normative task, proposition, evidence requirement, output subclause and control from both XML files is inventoried. PASS is clause-scoped, not production certification. Unresolved conditional applicability remains mandatory; only compiler/nonmandatory/inactive scopes are explicitly excluded.','','| ID | Authority | Mandatory | State | Requirement | Evidence / disposition |','|---|---|---|---|---|---|']
    esc=lambda s:str(s).replace('|','\\|').replace('\n',' ')
    for r in rows:lines.append('| '+' | '.join(map(esc,[r['id'],r['authority'],r['mandatory'],r['status'],r['expected_behavior'],r['reason']+'; '+', '.join(r['evidence'])]))+' |')
    (ROOT/'REQUIREMENTS_TRACEABILITY.md').write_text('\n'.join(lines)+'\n')
    return result

if __name__=='__main__':
    result=build();print('Inventoried',len(result['requirements']),'requirement/control rows')
