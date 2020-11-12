from typing import Union, Optional, Any
import traceback
from .engine import eval, Expression, Scope, MacroFunctionType
from .parser import parse
from .builtins import builtin_variables, builtin_macros
from ._version import __version__


def run(
    expr: Union[Expression, str, None] = None,
    *,
    filename: Optional[str] = None,
    variable_scope: Optional['Scope[Expression]'] = None,
    macro_scope: Optional['Scope[MacroFunctionType]'] = None
) -> Any:
    if isinstance(expr, Expression):
        return eval(expr, variable_scope=variable_scope, macro_scope=macro_scope)
    else:
        parsed_expr = parse(expr, filename=filename)
        return eval(parsed_expr, variable_scope=variable_scope, macro_scope=macro_scope)


def repl() -> None:
    variables = Scope(builtin_variables)
    macros = Scope(builtin_macros)
    print(f"Kaleb's Shitty LISP\nversion {__version__}")
    while True:
        print("> ", end="")
        try:
            expr = input()
        except KeyboardInterrupt:
            print()
            print("Exiting REPL")
            return
        try:
            res = run(expr, variable_scope=variables, macro_scope=macros)
        except KeyboardInterrupt:
            print("Killing expression evaluation")
        except Exception:
            traceback.print_exc()
        else:
            print(repr(res))
