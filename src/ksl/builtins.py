from typing import TypeVar, Optional, Callable, Any
from .engine import Expression, Scope, MacroFunctionType, Literal, ListExpression, ValueType, Name, Function


builtin_variables = Scope[Expression]()

builtin_macros = Scope[MacroFunctionType]()


T = TypeVar('T')


def builtin_function(name: Optional[str] = None) -> Callable[[T], T]:
    def wrapper(func: T) -> T:
        localname = name if name is not None else func.__qualname_  # type: ignore
        builtin_variables[localname] = Literal(func)
        return func
    return wrapper


def builtin_macro(name: Optional[str] = None) -> Callable[[T], T]:
    def wrapper(func: T) -> T:
        localname = name if name is not None else func.__qualname_  # type: ignore
        builtin_macros[localname] = func
        return func
    return wrapper


@builtin_function('int')
def int_constructor(arg: Expression) -> int:
    lit = arg.eval()
    return int(lit)


@builtin_function('float')
def float_constructor(arg: Expression) -> float:
    lit = arg.eval()
    return float(lit)


@builtin_function('str')
def str_constructor(arg: Expression) -> float:
    lit = arg.eval()
    return str(lit)


@builtin_function('+')
def add(a: Expression, b: Expression) -> Any:
    a_val = a.eval()
    b_val = b.eval()
    return a_val + b_val


@builtin_function('-')
def sub(a: Expression, b: Expression) -> Any:
    a_val = a.eval()
    b_val = b.eval()
    return a_val - b_val


@builtin_function('*')
def mul(a: Expression, b: Expression) -> Any:
    a_val = a.eval()
    b_val = b.eval()
    return a_val * b_val


@builtin_function('/')
def div(a: Expression, b: Expression) -> Any:
    a_val = a.eval()
    b_val = b.eval()
    return a_val / b_val


@builtin_function('%')
def mod(a: Expression, b: Expression) -> Any:
    a_val = a.eval()
    b_val = b.eval()
    return a_val % b_val


@builtin_function('=')
def eq(a: Expression, b: Expression) -> Any:
    a_val = a.eval()
    b_val = b.eval()
    return a_val == b_val


@builtin_function('!=')
def neq(a: Expression, b: Expression) -> Any:
    a_val = a.eval()
    b_val = b.eval()
    return a_val != b_val


@builtin_function('<=')
def le(a: Expression, b: Expression) -> Any:
    a_val = a.eval()
    b_val = b.eval()
    return a_val <= b_val


@builtin_function('>=')
def ge(a: Expression, b: Expression) -> Any:
    a_val = a.eval()
    b_val = b.eval()
    return a_val >= b_val


@builtin_function('<')
def lt(a: Expression, b: Expression) -> Any:
    a_val = a.eval()
    b_val = b.eval()
    return a_val < b_val


@builtin_function('>')
def gt(a: Expression, b: Expression) -> Any:
    a_val = a.eval()
    b_val = b.eval()
    return a_val > b_val


@builtin_function('if')
def iffunc(cond: Expression, a: Expression, b: Expression) -> Any:
    if cond.eval():
        return a.eval()
    else:
        return b.eval()


@builtin_function('cond')
def cond(*args: Expression) -> Any:
    if len(args) % 2 != 1:
        raise TypeError("Incorrect number of arguments")
    for i in range(0, len(args) - 1, 2):
        check, res = args[i:(i + 2)]
        if check.eval():
            return res.eval()
    return args[-1].eval()


@builtin_function('do')
def dofunc(statement: Expression, *statements: Expression) -> Any:
    if statements:
        res_expr = statements[-1]
    else:
        res_expr = statement
    return res_expr.eval()


@builtin_function('eval')
def evalfunc(expr: Expression) -> Any:
    from .run import run
    expr_str = expr.eval()
    return run(expr_str)


@builtin_macro('def')
def define(sexpr: ListExpression, vars: Scope[ValueType], macros: Scope[MacroFunctionType]) -> Expression:
    _, func_name, params, body = sexpr
    for param in params:
        if not isinstance(param, Name):
            raise TypeError()
    bound = body.bind(vars, macros)
    func = Function(params=params, body=bound, name=func_name)
    func_expr = Literal(func)
    vars._parent[func_name] = func_expr
    return func_expr


@builtin_macro('let')
def let(sexpr: ListExpression, vars: Scope[ValueType], macros: Scope[MacroFunctionType]) -> Expression:
    _, variable_name, expr = sexpr
    bound = expr.bind(vars, macros)
    vars._parent[variable_name] = bound
    return expr


@builtin_macro('lambda')
def lambdafunc(sexpr: ListExpression, vars: Scope[ValueType], macros: Scope[MacroFunctionType]) -> Expression:
    _, params, body = sexpr
    for param in params:
        if not isinstance(param, Name):
            raise TypeError()
    bound = body.bind(vars, macros)
    func = Function(params=params, body=bound)
    return Literal(func)
