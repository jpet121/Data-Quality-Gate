"""Direct checks derived from Development XML p_14/p_16, not event business rules."""
import ast
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

def test_application_has_python_312_syntax_and_explicit_callable_annotations():
    files=list((ROOT/'src/event_validator').glob('*.py'))+[ROOT/'main.py']
    assert files
    for path in files:
        tree=ast.parse(path.read_text(),filename=str(path),feature_version=(3,12))
        for node in ast.walk(tree):
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
                assert node.returns is not None,(path,node.name,'return')
                args=node.args.posonlyargs+node.args.args+node.args.kwonlyargs
                args += [a for a in [node.args.vararg,node.args.kwarg] if a is not None]
                for arg in args:
                    if arg.arg not in {'self','cls'}:
                        assert arg.annotation is not None,(path,node.name,arg.arg)
