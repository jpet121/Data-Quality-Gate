import json
from pathlib import Path
import pytest
from event_validator import validate,validate_many
from event_validator.parser import tokenize,ParseFault
from assurance.reference import lex
from assurance.campaign import run

ROOT=Path(__file__).resolve().parents[2]
MATRIX=json.loads((ROOT/'specifications/authorized_functional_baseline_v2/examples/matrix_v1.json').read_text())
REQUIRED=[(i,name) for i,event in enumerate(MATRIX['events']) for name in event['required']]

def render(fields):
    return ' | '.join(key+'="'+value.replace('\\','\\\\').replace('"','\\"').replace('|','\\|')+'"' for key,value in fields.items())

@pytest.mark.parametrize(('event','field'),REQUIRED)
def test_every_declared_required_field_is_enforced(cfg,valid,event,field):
    fields=lex(valid[event],32)
    key=field if field in fields else next(alias for alias,name in MATRIX['aliases'].items() if name==field)
    del fields[key]
    assert validate(render(fields),'missing-field',cfg).status=='REJECTED'

@pytest.mark.parametrize('event',range(5))
def test_each_schema_forbids_undeclared_fields(cfg,valid,event):
    assert validate(valid[event]+' | unexpected=VALUE','extra-field',cfg).status=='REJECTED'

@pytest.mark.parametrize('identifier',['A','A'*64,'0','A_0-9'])
def test_identifier_valid_boundaries(cfg,valid,identifier):
    fields=lex(valid[1],32);fields['event_id']=identifier
    assert validate(render(fields),'identifier',cfg).status=='ACCEPTED'

@pytest.mark.parametrize('identifier',['','A'*65,'_bad','-bad','é','A.B'])
def test_identifier_invalid_boundaries(cfg,valid,identifier):
    fields=lex(valid[1],32);fields['event_id']=identifier
    assert validate(render(fields),'identifier',cfg).status=='REJECTED'

def test_utf8_byte_limit_is_not_character_count(cfg):
    assert validate('🙂'*1024,'bytes',cfg).failure_category.value!='INPUT_LIMIT'
    assert validate('🙂'*1024+'a','bytes',cfg).failure_category.value=='INPUT_LIMIT'

def test_exact_token_budget(cfg):
    assert len(tokenize(' | '.join('k'+str(i)+'=v' for i in range(32)),32))==32
    with pytest.raises(ParseFault):tokenize(' | '.join('k'+str(i)+'=v' for i in range(33)),32)

def test_default_batch_limit_has_no_silent_truncation(cfg,valid):
    stream=validate_many((valid[1] for _ in range(10001)),'batch',cfg)
    for expected_index in range(10000):assert next(stream).index==expected_index
    with pytest.raises(ValueError,match='batch_limit'):next(stream)

def test_campaign_positive_and_negative_controls():
    report=run(64,1701)
    assert report['passed'],report
    assert report['outcomes']['VALID_AGREEMENT']>0
    assert report['outcomes']['PERMITTED_REJECTION_AGREEMENT']>0
    assert report['attempted']==report['compared']==64

IDENTIFIERS=[(i,name) for i,event in enumerate(MATRIX['events'])
             for name,kind in event['field_types'].items()
             if kind=='str' and name not in {'event_type','source','currency','reason'}]

@pytest.mark.parametrize(('event','field'),IDENTIFIERS)
def test_each_identifier_field_enforces_its_full_boundary(cfg,valid,event,field):
    original=lex(valid[event],32)
    key=field if field in original else next(alias for alias,name in MATRIX['aliases'].items() if name==field)
    for invalid in ['', 'A'*65,'_bad','-bad','é','A.B','A\n']:
        fields={**original,key:invalid}
        assert validate(render(fields),'all-identifiers',cfg).status=='REJECTED',(event,field,invalid)
    for accepted in ['A','0','A'*64,'A_0-9']:
        assert validate(render({**original,key:accepted}),'all-identifiers',cfg).status=='ACCEPTED',(event,field)

@pytest.mark.parametrize('event',[2,3])
def test_both_quantity_event_types_enforce_boundaries(cfg,valid,event):
    fields=lex(valid[event],32)
    for quantity in ['0','-1','1000001','1.5','1e1','+1']:
        assert validate(render({**fields,'quantity':quantity}),'quantity',cfg).status=='REJECTED'
    for quantity in ['1','1000000']:
        assert validate(render({**fields,'quantity':quantity}),'quantity',cfg).status=='ACCEPTED'

def test_authorized_matrix_defaults_and_content_hash_are_stable(cfg,tmp_path):
    from event_validator import load_matrix
    assert (cfg.version,cfg.max_event_bytes,cfg.max_tokens,cfg.max_batch)==(
        MATRIX['version'],MATRIX['limits']['max_event_bytes'],MATRIX['limits']['max_tokens'],MATRIX['limits']['max_batch'])
    assert dict(cfg.aliases)==MATRIX['aliases']
    path=tmp_path/'same-content.json';path.write_text(json.dumps(MATRIX,sort_keys=True,separators=(',',':')))
    assert load_matrix(path).fingerprint==cfg.fingerprint


def test_reduced_budgets_are_loaded_and_enforced(tmp_path,valid):
    from event_validator import load_matrix
    data=json.loads(json.dumps(MATRIX));data['limits']={'max_event_bytes':16,'max_tokens':2,'max_batch':2}
    path=tmp_path/'limited.json';path.write_text(json.dumps(data));limited=load_matrix(path)
    assert validate(valid[0],'limited',limited).failure_category.value=='INPUT_LIMIT'
    events=validate_many(['a=v']*3,'limited',limited)
    next(events);next(events)
    with pytest.raises(ValueError,match='batch_limit'):next(events)
    with pytest.raises(ParseFault):tokenize('a=v | b=v | c=v',limited.max_tokens)

@pytest.mark.parametrize('shadow_first',[False,True])
def test_unique_highest_priority_wins_independent_of_config_order(tmp_path,valid,shadow_first):
    from event_validator import load_matrix
    data=json.loads(json.dumps(MATRIX));shadow=json.loads(json.dumps(data['events'][0]))
    shadow['schema_id']='ORDER_CREATED_PRIORITY';shadow['matcher']['priority']=100
    if shadow_first:data['events'].insert(0,shadow)
    else:data['events'].append(shadow)
    path=tmp_path/'priority.json';path.write_text(json.dumps(data));configured=load_matrix(path)
    outcome=validate(valid[0],'priority',configured)
    assert outcome.status=='ACCEPTED' and outcome.schema_id=='ORDER_CREATED_PRIORITY'


def test_all_schema_metadata_and_original_input_hashes_match_the_spec(cfg,valid):
    import hashlib
    assert len(valid)==len(MATRIX['events'])
    for event,raw in zip(MATRIX['events'],valid):
        result=validate(raw,'schema-metadata',cfg)
        assert result.status=='ACCEPTED'
        assert (result.event_type,result.schema_id,result.schema_version)==(event['event_type'],event['schema_id'],event['schema_version'])
        assert result.config_fingerprint==cfg.fingerprint
        assert result.input_sha256==hashlib.sha256(raw.encode('utf-8')).hexdigest()
