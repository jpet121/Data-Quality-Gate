import importlib.util
from pathlib import Path
import pytest

path=Path(__file__).resolve().parents[2]/'verification/mutation_check.py'
spec=importlib.util.spec_from_file_location('mutation_runner',path)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

@pytest.mark.parametrize(('code','counts','timeout','expected'),[
 (1,{'total':2,'failed':1,'errors':0,'skipped':0},False,'killed'),
 (1,{'total':2,'failed':1,'errors':1,'skipped':0},False,'harness_error'),
 (0,{'total':2,'failed':0,'errors':0,'skipped':0},False,'survived'),
 (0,{'total':0,'failed':0,'errors':0,'skipped':0},False,'harness_error'),
 (2,None,False,'harness_error'), (124,None,True,'timed_out'),
 (0,{'total':2,'failed':0,'errors':0,'skipped':1},False,'harness_error'),
])
def test_mutant_accounting_distinguishes_detection_from_harness_failure(code,counts,timeout,expected):
    assert module.classify(code,counts,timeout)==expected
