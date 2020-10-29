from typing import Any, Union, Protocol, Dict, List
from functools import cached_property


__version__ = '0.1.dev0'


class Expression(Protocol):

    def inspect(self) -> Any:
        pass

    def eval(self, scope: 'Scope') -> 'LazyValue':
        pass

    def print(self) -> str:
        pass


class LazyValue(Protocol):

    def value(self) -> Any:
        pass


class Scope:

    def __init__(self, parent: Union[None, 'Scope'] = None):
        self._scope: Dict[str, 'LazyValue'] = {}
        self._parent = parent

    @property
    def parent(self) -> Union[None, 'Scope']:
        return self._parent

    def __getitem__(self, item: str) -> 'LazyValue':
        if item in self._scope:
            return self._scope[item]
        elif self._parent is None:
            raise KeyError(item)
        else:
            return self._parent[item]

    def __setitem__(self, item: str, value: 'LazyValue'):
        self._scope[item] = value


class LazyLiteral:

    def __init__(self, value: Any):
        self._value = value

    def value(self) -> Any:
        return self._value


class Literal(Expression):

    def __init__(self, value: Any, **info: Any):
        self._info = info
        self._value = value

    @property
    def info(self) -> Dict[str, Any]:
        return self._info

    def inspect(self) -> str:
        return self._value

    def eval(self, scope: Scope) -> LazyValue:
        return LazyLiteral(self._value)

    def print(self) -> str:
        return repr(self._value)


def Eval(expr: Expression, scope: Union[None, Scope] = None) -> Any:
    if scope is None:
        scope = Scope()
    result = expr.eval(scope)
    return result.value()


def Print(expr: Expression) -> str:
    return expr.print()
