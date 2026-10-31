"""Independent .split reference is only correct for unquoted alnum words."""
import itertools
from event_validator.parser import tokenize

def reference_parse(text):
    out={}
    for part in text.split(' | '):
        k,v=part.split('=',1)
        assert k not in out
        out[k]=v
    return out

def test_differential_restricted_subset():
    fields=['a=ALPHA','b=BRAVO','c=CHARLIE']
    for seq in itertools.permutations(fields):
        s=' | '.join(seq)
        assert dict(tokenize(s,10))==reference_parse(s)
