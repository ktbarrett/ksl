from typing import Any, Union, Protocol, Dict, List
from .utils import cached


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


class LazyLiteral(LazyValue):

    def __init__(self, value: Any):
        self._value = value

    @cached
    def value(self) -> Any:
        return self._value


class LazyFunctionCall(LazyValue):

    def __init__(self, func: LazyValue, args: List[LazyValue]):
        self._func = func
        self._args = args

    @cached
    def value(self) -> Any:
        func = self._func.value()
        return func(*self._args)


class Literal(Expression):

    def __init__(self, value: Any, **info: Any):
        self._info = info
        self._value = value

    @property
    def info(self) -> Dict[str, Any]:
        return self._info

    def inspect(self) -> Any:
        return self._value

    def eval(self, scope: Scope) -> LazyValue:
        return LazyLiteral(self._value)

    def print(self) -> str:
        return repr(self._value)


class Name(Expression):

    def __init__(self, name: str, **info: Any):
        self._name = name
        self._info = info

    @property
    def info(self) -> Dict[str, Any]:
        return self._info

    def inspect(self) -> str:
        return self._name

    def eval(self, scope: Scope) -> LazyValue:
        return scope[self._name]

    def print(self) -> str:
        return self._name


class ListExpression(Expression):

    def __init__(self, sub_expressions: List[Expression], **info: Any):
        self._sub_expressions = sub_expressions
        self._info = info

    @property
    def info(self) -> Dict[str, Any]:
        return self._info

    def inspect(self) -> List[Expression]:
        return self._sub_expressions

    def eval(self, scope: Scope) -> LazyValue:
        # enter a new scope
        scope = Scope(parent=scope)
        # evaluate each element
        sub_expressions = [e.eval(scope) for e in self._sub_expressions]
        # call function lazily
        func, *args = sub_expressions
        return LazyFunctionCall(func, args)

    def print(self) -> str:
        return '(' + ' '.join(e.print() for e in self._sub_expressions) + ')'


def Eval(expr: Expression, scope: Union[None, Scope] = None) -> Any:
    if scope is None:
        scope = Scope()
    result = expr.eval(scope)
    return result.value()


def Print(expr: Expression) -> str:
    return expr.print()
