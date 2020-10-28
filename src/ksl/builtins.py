from typing import Callable, Any, Union, List
from . import Scope, Evaluatable, Name, Expression


Function = Callable[[Scope, Evaluatable, ...]]


builtins = {}


def builtin(func: Union[str, Function]):
    if type(func) is str:
        name = func

        def wrapper(func: Function):
            builtins[name] = func
            return func
        return wrapper
    else:
        builtins[func.__name__] = func
        return func


@builtin('+')
def add(scope: Scope, a: Evaluatable, b: Evaluatable) -> Any:
    return a.eval(scope) + b.eval(scope)


@builtin('-')
def sub(scope: Scope, a: Evaluatable, b: Evaluatable) -> Any:
    return a.eval(scope) - b.eval(scope)


@builtin('*')
def mul(scope: Scope, a: Evaluatable, b: Evaluatable) -> Any:
    return a.eval(scope) * b.eval(scope)


@builtin('/')
def div(scope: Scope, a: Evaluatable, b: Evaluatable) -> Any:
    return a.eval(scope) / b.eval(scope)


@builtin
def let(scope: Scope, name: Name, value: Evaluatable) -> Any:
    if not isinstance(name, Name):
        raise TypeError(f"Variable name is not a Name: '{name.print()}'")
    name = name.inspect()
    value = value.eval(scope)
    scope.parent[name] = value
    return value


class _Function:

    def __init__(self, params: List[str], body: Expression):
        self._params = params
        self._body = body

    def __call__(self, scope: Scope, *args: Evaluatable):
        pass


@builtin
def define(scope: Scope, name: Name, params: Expression, body: Expression) -> Function:
    if not isinstance(name, Name):
        raise TypeError(f"Function name is not a Name: '{name.print()}'")
    name = name.inspect()

    if not isinstance(params, Expression):
        raise TypeError
    params = params.inspect()
    for i, param in enumerate(params):
        if not isinstance(param, Name):
            raise TypeError(f"Function parameter {i} is not a Name: '{param.print()}'")
    params = [param.inspect() for param in params]

    func = _Function(params, body)
    scope.parent[name] = func
    return func
