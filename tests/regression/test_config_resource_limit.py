"""Configuration size limit must hold before large file contents are allocated."""
import subprocess
import sys
from pathlib import Path
import pytest
from event_validator import load_matrix
from event_validator.matrix import ConfigError


def test_oversized_configuration_is_rejected_under_memory_budget(tmp_path):
    path=tmp_path/'oversized.json'
    with path.open('wb') as stream:stream.truncate(63*1024**2)
    code='''import resource,sys
sys.path.insert(0,sys.argv[1])
resource.setrlimit(resource.RLIMIT_AS,(64*1024**2,64*1024**2))
from event_validator import load_matrix
from event_validator.matrix import ConfigError
try:
    load_matrix(sys.argv[2])
except ConfigError:
    print('CONTROLLED_CONFIG_REJECTION')
else:
    raise AssertionError('oversized configuration accepted')
'''
    root=Path(__file__).resolve().parents[2]
    p=subprocess.run([sys.executable,'-I','-c',code,str(root/'src'),str(path)],capture_output=True,text=True,timeout=10)
    assert p.returncode==0,(p.stdout,p.stderr)
    assert p.stdout.strip()=='CONTROLLED_CONFIG_REJECTION'


def test_deep_invalid_configuration_is_a_typed_error(tmp_path):
    path=tmp_path/'deep.json';path.write_text('['*10000+'0'+']'*10000)
    with pytest.raises(ConfigError):load_matrix(path)


def test_deep_nested_event_is_a_controlled_schema_rejection(cfg,valid):
    from dataclasses import replace
    from event_validator import validate
    # Supported loader safety ceiling; default 4-KiB budgets reject this earlier.
    configured=replace(cfg,max_event_bytes=65536)
    prefix=valid[0].split(' | lines_json=')[0]
    raw=prefix+' | lines_json="'+'['*10000+'0'+']'*10000+'"'
    result=validate(raw,'deep-event',configured)
    assert result.status=='REJECTED' and result.failure_category.value=='SCHEMA_VIOLATION'
