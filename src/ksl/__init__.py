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


class Scope:

    def __init__(self, parent: Union[None, 'Scope']):
        self._scope: Dict[str, 'LazyValue'] = {}
        self._parent = parent

    @property
    def parent(self) -> 'Scope':
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


class LazyValue:

    @classmethod
    def from

    @cached_property
    def value(self) -> Any:
        pass  # TODO


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
        scope = Scope(parent=scope)
        sub_expressions = [expr.eval(scope) for expr in self._sub_expressions]
        func, *args = sub_expressions
        return LazyValue.from_expression()

    def print(self) -> str:
        return '(' + ' '.join(e.print() for e in self._sub_expressions) + ')'


class Name(Expression):

    def __init__(self, name: str, **info: Any):
        super().__init__(**info)
        self._name = name

    @property
    def info(self) -> Dict[str, Any]:
        return self._info

    def inspect(self) -> str:
        return self._name

    def eval(self, scope: Scope) -> LazyValue:
        return scope[self._name]

    def print(self) -> str:
        return self._name


class Literal(Expression):

    def __init__(self, value: Any, **info: Any):
        super().__init__(**info)
        self._value = value

    @property
    def info(self) -> Dict[str, Any]:
        return self._info

    def inspect(self) -> str:
        return self._value

    def eval(self, scope: Scope) -> LazyValue:
        return LazyValue.from_value(self._value)

    def print(self) -> str:
        return repr(self._value)


def Eval(expr: Expression, scope: Scope) -> Any:
    return expr.eval(scope).value


def Print(expr: Expression) -> str:
    return expr.print()
