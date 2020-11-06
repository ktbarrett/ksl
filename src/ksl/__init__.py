from typing import Union, Optional, Any
from .engine import eval, Expression, Scope, MacroFunctionType
from .parser import parse

__version__ = '0.1.dev0'


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
