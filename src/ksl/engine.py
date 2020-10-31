from typing import Any, Union, Protocol, Dict, List, TypeVar, Generic
from .utils import cached
from .types import ValueType, MacroFunctionType


class Expression(Protocol):

    def inspect(self) -> Any:
        pass

    def bind(self, variable_scope: 'Scope[Expression]', macro_scope: 'Scope[MacroFunctionType]') -> 'Expression':
        pass

    def eval(self) -> ValueType:
        pass

    def print(self) -> str:
        pass


T = TypeVar('T')


class Scope(Generic[T]):

    def __init__(self, parent: Union[None, 'Scope[T]'] = None):
        self._scope: Dict[str, T] = {}
        self._parent = parent

    @property
    def parent(self) -> Union[None, 'Scope[T]']:
        return self._parent

    def __getitem__(self, item: str) -> T:
        if item in self._scope:
            return self._scope[item]
        elif self._parent is None:
            raise KeyError(item)
        else:
            return self._parent[item]

    def __setitem__(self, item: str, value: T):
        self._scope[item] = value


class Literal(Expression):

    def __init__(self, value: ValueType, **info: Any):
        self._info = info
        self._value = value

    @property
    def info(self) -> Dict[str, Any]:
        return self._info

    def inspect(self) -> Any:
        return self._value

    def bind(self, variable_scope: Scope[Expression], macro_scope: Scope[MacroFunctionType]) -> Expression:
        return self

    def eval(self) -> ValueType:
        return self._value

    def print(self) -> str:
        return repr(self._value)


class Name(Expression):

    def __init__(self, name: str, **info: Any):
        self._name = name
        self._info = info

    @property
    def info(self) -> Dict[str, Any]:
        return self._info

    def bind(self, variable_scope: Scope[Expression], macro_scope: Scope[MacroFunctionType]) -> Expression:
        return variable_scope[self]

    def eval(self) -> ValueType:
        raise RuntimeError("Attempted evaluating unbound name")

    def inspect(self) -> str:
        return self._name

    def print(self) -> str:
        return self._name


class Parameter(Name):

    UNBOUND = object()

    def __init__(self, name: str, **info: Any):
        super().__init__(name, **info)
        self._value: Union[Literal['Name.UNBOUND'], ValueType] = type(self).UNBOUND

    def set_value(self, value: ValueType) -> None:
        if self._value is not type(self).UNBOUND:
            raise RuntimeError("Attempt to bind a new value to a name")
        self._value = value

    def eval(self) -> ValueType:
        if self._value is not type(self).UNBOUND:
            return self._value
        return super().eval()


class ListExpression(Expression):

    def __init__(self, sub_expressions: List[Expression], **info: Any):
        self._sub_expressions = sub_expressions
        self._info = info

    @property
    def info(self) -> Dict[str, Any]:
        return self._info

    def inspect(self) -> List[Expression]:
        return self._sub_expressions

    def bind(self, variable_scope: Scope[Expression], macro_scope: Scope[MacroFunctionType]) -> Expression:
        if len(self._sub_expressions) >= 1:
            func = self._sub_expressions[0]
            if isinstance(func, Name) and func.inspect() in macro_scope:
                macro = macro_scope[func]
                changed = macro(self)
                return changed.bind(variable_scope, macro_scope)
        for expr in self._sub_expressions:
            expr.bind(variable_scope, macro_scope)
        return self

    @cached
    def eval(self) -> ValueType:
        if len(self._sub_expressions) < 1:
            return None
        func, *args = self._sub_expressions
        func = func.eval()
        res = func(*args)
        return res

    def print(self) -> str:
        return '(' + ' '.join(e.print() for e in self._sub_expressions) + ')'


def Eval(expr: Expression, scope: Union[None, Scope] = None) -> Any:
    pass


def Print(expr: Expression) -> str:
    return expr.print()
