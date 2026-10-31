"""Requires optional Hypothesis dependency. Not silently omitted from reported test plan."""
import pytest
pytest.importorskip('hypothesis', reason='optional Hypothesis dependency not installed')
from hypothesis import given,settings,strategies as st,seed
from hypothesis.stateful import RuleBasedStateMachine,rule,invariant
from event_validator import validate
from event_validator.parser import tokenize,ParseFault

@seed(20261029)
@given(st.lists(st.sampled_from(['event','tenant','order','source','occurred_at','event_id']),min_size=1,max_size=20))
@settings(max_examples=150,deadline=None)
def test_duplicate_keys_never_accepted(cfg,keys):
    if len(set(keys))<len(keys):
        text=' | '.join(f'{k}=SAFE' for k in keys)
        assert validate(text,'property',cfg).status=='REJECTED'

@seed(1701)
@given(st.text(max_size=300))
@settings(max_examples=250,deadline=None)
def test_random_unicode_cannot_raise(cfg,s):
    a=validate(s,'fuzz',cfg)
    b=validate(s,'fuzz',cfg)
    assert a.canonical()==b.canonical()

@seed(23)
@given(st.lists(st.sampled_from(['a=1','b=2','c=3']),min_size=1,max_size=3,unique=True))
def test_lexer_stable_order(keys):
    assert dict(tokenize(' | '.join(keys),10))==dict(tokenize(' | '.join(reversed(keys)),10))

class LexerMachine(RuleBasedStateMachine):
    def __init__(self):super().__init__();self.pieces=[]
    @rule(key=st.sampled_from(['a','b','c']),value=st.text(alphabet='xyz',min_size=1,max_size=5))
    def append(self,key,value):self.pieces.append((key,value))
    @invariant()
    def duplicate_never_succeeds(self):
        sample=' | '.join(f'{k}={v}' for k,v in self.pieces)
        if len(set(k for k,v in self.pieces))<len(self.pieces):
            try:tokenize(sample,100)
            except ParseFault:return
            assert False,'duplicate key accepted'
TestLexerMachine=LexerMachine.TestCase
