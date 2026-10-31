"""Trace the owner-designated functional baseline to actual JUnit evidence."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'specifications/authorized_functional_baseline_v2'


def rows() -> list[dict]:
    data=json.loads((BASE/'examples/matrix_v1.json').read_text())
    report=ROOT/'continuation_evidence/final_suite.xml'
    executed=list(ET.parse(report).getroot().iter('testcase')) if report.exists() else []
    result=[]
    def add(key,text,source,selectors,exact=False):
        cases=[c for c in executed if any((c.get('name')==s if exact else (c.get('name','').startswith(s) or (c.get('classname','')+'.'+c.get('name','')).startswith(s))) for s in selectors)]
        good=bool(cases) and all(not any(c.find(tag)is not None for tag in ['failure','error','skipped']) for c in cases)
        result.append({'id':'F:'+key,'source_id':key,'authority':'functional (owner designated)','section':'Functional requirements','modality':'REQUIRED','mandatory':True,
          'source':{'file':str(BASE.relative_to(ROOT)/source.split('#')[0]),'location':source,'sha256':hashlib.sha256((BASE/source.split('#')[0]).read_bytes()).hexdigest()},
          'expected_behavior':text,'valid_input_domain':'Declared five-event data contract and documented strict input profile','invalid_input_domain':'Missing/extra fields, wrong lexical forms/types/bounds, malformed quoting, duplicate aliases or unsupported event types',
          'preconditions':'Approved example matrix; Python 3.12/Pydantic v2; disposable storage for integration checks',
          'postconditions':text,'invariants':'No guessed defaults, implicit business integrations, raw-value diagnostic leaks or silent input truncation',
          'required_error_behavior':'Controlled declared rejection/error; no incorrect accepted result',
          'interfaces':'load_matrix, validate, validate_many, repositories, dispatch_once and CLI as applicable',
          'verification_method':'Executed mapped tests plus independent reference/campaign evidence where applicable','oracle_basis':'Owner-authorized source documents; regex/stdlib/rational reference and checked Lean store model',
          'risk':'Local synthetic validator; no live business integrations','acceptance_criteria':text,'unresolved_assumptions':[] if good else ['Mapped required checks absent or nonpassing'],
          'status':'PASS' if good else 'BLOCKED','reason':str(len(cases))+' mapped executed cases; all must pass',
          'evidence':['continuation_evidence/final_suite.xml','continuation_evidence/final_collection.json'],
          'executed_test_ids':[c.get('classname','')+'.'+c.get('name','') for c in cases],'test_selectors':selectors,'scope_reason':''})
    requirements=[
      ('RAW_STRING','Non-string events reject without implicit conversion',['test_input_bounds','test_input_size_and_non_string_boundaries']),
      ('BYTE_BUDGET','Maximum event size is 4096 UTF-8 bytes by default',['test_utf8_byte_limit_is_not_character_count']),
      ('TOKEN_BUDGET','At most 32 tokens; excess tokens reject',['test_exact_token_budget']),
      ('BATCH_BUDGET','At most 10000 events by default; over-limit raises without silent truncation',['test_default_batch_limit_has_no_silent_truncation']),
      ('REDUCIBLE_BUDGETS','Configured reduced budgets are loaded and enforced',['test_reduced_budgets_are_loaded_and_enforced']),
      ('CONFIG_CONTENT','Data-only approved matrix loads with stable versioned content fingerprint',['test_authorized_matrix_defaults_and_content_hash_are_stable']),
      ('CONFIG_REGISTRY','Unknown registries and unsafe executable/regex matchers reject',['test_config_unknown_registry_and_unsafe_matcher','test_config_reject_unknown_registry']),
      ('CLASSIFY','Exact classification selects unique highest explicit priority and rejects ties',['test_unique_highest_priority_wins_independent_of_config_order','test_ambiguity']),
      ('LEXER','ASCII keys, quoting, explicit escapes, whitespace and delimiters obey the declared grammar',['test_parser_quote_and_escape','test_reference_quoted_grammar_has_independent_roundtrip']),
      ('DUPLICATES','Duplicate names and alias collisions reject even when values match',['test_duplicate_even_identical','test_alias_collision_and_exact_duplicate_reject']),
      ('STRICT','Strict frozen Pydantic models reject parser-bypass type violations',['test_strict_pydantic_rejects_string_decimal_and_naive_datetime','test_strict_model_without_lexer']),
      ('IMMUTABILITY','Accepted records, nested line items and loaded snapshots are immutable',['test_accepted_records_and_nested_values_are_immutable','test_matrix_is_deeply_immutable_and_identity_stable']),
      ('MONEY','Positive money has integer or <=2 fractional digits, no exponent, and documented 13-digit integer cap',['test_money_valid_boundaries','test_money_invalid_lexemes_or_bounds','test_nested_json_money_cannot_bypass_lexical_contract']),
      ('JSON_MONEY','Exact numeric JSON money includes integer notation; booleans, invalid scales and exponents reject',['test_json_integer_price_is_exact_money','test_json_bool_zero_or_negative_is_not_positive_money','test_allowed_nested_json_decimal_money_remains_valid']),
      ('EXACT_TOTAL','Optional line subtotal must match gross amount exactly without ambient rounding dependence',['test_exact_line_totals_are_independent_of_decimal_context','test_nested_duplicate_key_and_total_mismatch_reject']),
      ('QUANTITY','Inventory and shipment quantities are integers 1 through 1000000',['test_both_quantity_event_types_enforce_boundaries']),
      ('TIMESTAMP','Aware strict calendar timestamps use the owner-confirmed offset/fraction/uppercase profile',['test_timestamp_invalid_rejects','test_timestamp_valid_offsets']),
      ('ISOLATION','Valid-invalid-valid batches retain the two valid events',['test_batch_isolation']),
      ('DETERMINISM','Same input/config yields canonical deterministic output',['test_determinism','test_hypothesis_unicode_never_crashes']),
      ('DIAGNOSTICS','Rejected raw customer/payment values do not appear in diagnostics or trace',['test_no_sensitive_diagnostics','test_no_secret_leak_in_errors_or_trace']),
      ('INPUT_HASH','Input hashes cover original strings; outputs retain correct schema metadata',['test_all_schema_metadata_and_original_input_hashes_match_the_spec']),
      ('FULL_RECORD','Accepted serialization/persistence retains event-specific fields',['test_accepted_serialization_preserves_every_event_field','test_persistence_retains_complete_accepted_record']),
      ('ACID','Result/error/audit/outbox records persist atomically with FK enforcement',['test_transactions_idempotency_and_outbox','test_fault_rollback_on_invalid_fk','test_storage_transaction_rollback_on_outbox_insert_failure','test_pg_fault_rollback','test_pg_fk']),
      ('IDENTITY','Delivery identity includes tenant, event reference and config fingerprint',['test_same_event_id_in_two_valid_tenants_is_not_a_collision','test_same_tenant_event_under_distinct_snapshots_is_distinct','test_storage_cannot_persist_event_under_other_tenant_or_event_id']),
      ('REPLAY','Equal hashes deduplicate; changed content conflicts without partial writes',['test_id_collision_rollback','test_checked_idempotency_model_matches_sqlite_and_atomic_state','test_pg_collision_and_identity']),
      ('QUARANTINE','Rejected results create non-executable quarantine; only accepted events create runnable jobs',['test_transactions_idempotency_and_outbox','test_pg_persistence_reopen']),
      ('WORKFLOW','Dispatch is disabled by default; explicitly supplied local sink records delivery',['test_transactions_idempotency_and_outbox','test_pg_dispatch','test_dispatch_database_payload_representations']),
      ('RETRY','Failed local delivery retries, then dead-letters at the default maximum',['test_retry_dead_letter','test_pg_retry_dead_letter']),
      ('POSTGRES','Optional PostgreSQL persistence, reopen, contention and claiming behave correctly',['test_pg_persistence_reopen','test_pg_concurrent_insert','test_pg_concurrent_claim_and_finish']),
      ('STANDALONE','Generated main.py runs independently of a local package and matches package behavior',['test_standalone_cli_without_local_package','test_standalone_script_matches_package_replay']),
      ('CLI_FAILURE','CLI persistence/input/config failures do not report successful completion',['test_cli_returns_nonzero','test_cli_storage','test_cli_invalid','test_standalone_cli_without_local_package']),
      ('CONTROLLED_INVALID','Invalid Unicode and malformed/oversized/deep inputs reject predictably',['test_release_invalid_unicode_must_not_crash','test_oversized_configuration_is_rejected_under_memory_budget','test_deep_invalid_configuration_is_a_typed_error','test_deep_nested_event_is_a_controlled_schema_rejection']),
    ]
    for key,text,selectors in requirements:add(key,text,'README.md',selectors)
    for name,value in data['limits'].items():add('LIMIT_'+name,str(name)+' defaults to '+str(value),'examples/matrix_v1.json#/limits/'+name,['test_authorized_matrix_defaults_and_content_hash_are_stable'])
    for alias,canonical in data['aliases'].items():add('ALIAS_'+alias,alias+' normalizes only to '+canonical,'examples/matrix_v1.json#/aliases/'+alias,['test_authorized_matrix_defaults_and_content_hash_are_stable','test_alias_collision_and_exact_duplicate_reject'])
    for i,event in enumerate(data['events']):
        base='examples/matrix_v1.json#/events/'+str(i)
        for key in ['event_type','schema_id','schema_version','registry_key']:
            add(event['event_type']+'_'+key,key+' is '+event[key],base+'/'+key,['test_all_schema_metadata_and_original_input_hashes_match_the_spec','test_all_event_models_agree_with_independent_reference'])
        for name in event['required']:
            add(event['event_type']+'_required_'+name,name+' is required for '+event['event_type'],base+'/required',['test_every_declared_required_field_is_enforced['+str(i)+'-'+name+']'],True)
        for name in event['optional']:
            add(event['event_type']+'_optional_'+name,name+' is optional and validated when present',base+'/optional',['test_all_event_models_agree_with_independent_reference','test_campaign_positive_and_negative_controls'])
        for name,kind in event['field_types'].items():
            add(event['event_type']+'_type_'+name,name+' uses declared kind '+kind,base+'/field_types/'+name,['test_all_event_models_agree_with_independent_reference','test_reference_known_valid_and_invalid_cases'])
        add(event['event_type']+'_extra_forbidden','Undeclared fields are forbidden',base,['test_each_schema_forbids_undeclared_fields['+str(i)+']'],True)
    # Acceptance predicates add no rules beyond their explicit authoritative text.
    for number,line in enumerate((BASE/'docs/ACCEPTANCE.md').read_text().splitlines(),1):
        if line.startswith('| ') and not line.startswith('| Contract'):
            parts=[p.strip() for p in line.split('|')[1:-1]]
            if len(parts)==3:
                import re
                selectors=re.findall(r'`([^`]+)`',parts[2])
                if parts[0]=='Hypothesis fuzz':selectors=['tests.property.test_properties.']
                if parts[0]=='Scale':
                    add('ACCEPTANCE_'+str(number),parts[0]+': '+parts[1],'docs/ACCEPTANCE.md#L'+str(number),[])
                    measurements=[]
                    for name in ['benchmark_parse.json','benchmark_sqlite.json']:
                        path=ROOT/'continuation_evidence'/name
                        if path.exists():measurements.append(json.loads(path.read_text()))
                    good=len(measurements)==2 and all(m['count']>0 and m['accepted']+m['rejected']==m['count'] for m in measurements)
                    result[-1].update(status='PASS' if good else 'BLOCKED',reason='Actual seeded parsing and SQLite benchmark measurements; no performance SLO invented',evidence=['continuation_evidence/benchmark_parse.json','continuation_evidence/benchmark_sqlite.json'],unresolved_assumptions=[] if good else ['benchmark measurements unavailable'])
                else:add('ACCEPTANCE_'+str(number),parts[0]+': '+parts[1],'docs/ACCEPTANCE.md#L'+str(number),selectors)
    return result
