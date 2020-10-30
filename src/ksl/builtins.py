from typing import Callable, Any, Union, Dict
from . import Scope, LazyValue


Function = Callable[[LazyValue], Any]


builtins: Dict[str, Function] = {}


def builtin(func: Union[str, Function]):
    if isinstance(func, str):
        name = func

        def wrapper(func: Function):
            builtins[name] = func
            return func
        return wrapper
    else:
        builtins[func.__name__] = func
        return func


@builtin('+')
def add(a: LazyValue, b: LazyValue) -> Any:
    a = a.value()
    b = b.value()
    return a + b


@builtin('-')
def sub(a: LazyValue, b: LazyValue) -> Any:
    a = a.value()
    b = b.value()
    return a - b


@builtin('*')
def mul(a: LazyValue, b: LazyValue) -> Any:
    a = a.value()
    b = b.value()
    return a * b


@builtin('/')
def div(a: LazyValue, b: LazyValue) -> Any:
    a = a.value()
    b = b.value()
    return a / b
