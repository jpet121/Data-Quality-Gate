"""Exact totals and deterministic results must not depend on ambient Decimal precision."""
from decimal import localcontext,ROUND_DOWN,ROUND_UP,ROUND_HALF_EVEN
import pytest
from event_validator import validate

@pytest.mark.parametrize('precision',[1,2,3,28])
@pytest.mark.parametrize('rounding',[ROUND_DOWN,ROUND_UP,ROUND_HALF_EVEN])
def test_exact_line_totals_are_independent_of_decimal_context(cfg,valid,precision,rounding):
    base=valid[0].split(' | lines_json=')[0].replace('gross_amount=25.00','gross_amount=12.34')
    payload='[{"sku_code":"SKU-A","quantity":1,"unit_price":"12.34"}]'
    raw=base+' | lines_json="'+payload.replace('"','\\"')+'"'
    baseline=validate(raw,'decimal-context',cfg)
    assert baseline.status=='ACCEPTED'
    with localcontext() as ctx:
        ctx.prec=precision;ctx.rounding=rounding
        actual=validate(raw,'decimal-context',cfg)
    assert actual.canonical()==baseline.canonical()
