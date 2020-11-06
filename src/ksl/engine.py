from typing import Any, Union, Dict, List, TypeVar, Callable, Optional, Iterable
from abc import ABC, abstractmethod
from .utils import cached


ValueType = Any

FunctionType = Callable[[List['Expression']], 'ValueType']

# mypy does not support this in any way
# MacroFunctionType = Callable[['ListExpression', 'Scope[ValueType]', 'Scope[MacroFunctionType]'], 'Expression']
MacroFunctionType = Callable[['ListExpression', 'Scope[ValueType]', 'Scope'], 'Expression']


T = TypeVar('T')


def eval(
    expr: 'Expression',
    variable_scope: Optional['Scope[Expression]'] = None,
    macro_scope: Optional['Scope[MacroFunctionType]'] = None
) -> Any:
    from .builtins import builtin_variables, builtin_macros  # noqa: E402
    if variable_scope is None:
        variable_scope = builtin_variables
    if macro_scope is None:
        macro_scope = builtin_macros
    bound = expr.bind(variable_scope, macro_scope)
    return bound.eval()


class Expression(ABC):

    @abstractmethod
    def bind(self, variable_scope: 'Scope[Expression]', macro_scope: 'Scope[MacroFunctionType]') -> 'Expression':
        pass  # pragma: no cover

    @abstractmethod
    def eval(self) -> ValueType:
        pass  # pragma: no cover


class Scope(Dict[str, T]):

    def __init__(self, parent: Union[None, Dict[str, T]] = None):
        super().__init__()
        self._parent = parent

    @property
    def parent(self) -> Union[None, Dict[str, T]]:
        return self._parent

    def __getitem__(self, item: str) -> T:
        if item in self:
            return super().__getitem__(item)
        elif self._parent is not None:
            return self._parent[item]
        else:
            raise KeyError(repr(item))


class Literal(Expression):

    def __init__(self, value: T, **info: Any):
        self._value = value
        self._info = info

    @property
    def value(self) -> T:
        return self._value

    @property
    def info(self) -> Dict[str, Any]:
        return self._info  # pragma: no cover

    def bind(self, variable_scope: Scope[Expression], macro_scope: Scope[MacroFunctionType]) -> Expression:
        return self

    @cached
    def eval(self) -> ValueType:
        return self._value


class Name(str, Expression):
    _info: Dict[str, Any]

    def __new__(cls, name: str, **info: Any):
        s = str.__new__(cls, name)
        s._info = info
        return s

    @property
    def info(self) -> Dict[str, Any]:
        return self._info  # pragma: no cover

    def bind(self, variable_scope: Scope[Expression], macro_scope: Scope[MacroFunctionType]) -> Expression:
        try:
            expr = variable_scope[self]
        except KeyError:
            return self
        else:
            return expr

    def eval(self) -> ValueType:
        raise RuntimeError("Attempted evaluating unbound name")


class ListExpression(tuple, Expression):
    _info: Dict[str, Any]

    def __new__(cls, sub_expressions: Iterable[Expression], **info: Any):
        if not sub_expressions:
            raise ValueError("List expressions cannot be empty")
        s = tuple.__new__(cls, sub_expressions)
        s._info = info
        return s

    @property
    def info(self) -> Dict[str, Any]:
        return self._info  # pragma: no cover

    def bind(self, variable_scope: Scope[Expression], macro_scope: Scope[MacroFunctionType]) -> Expression:
        func = self[0]
        if isinstance(func, Name) and func in macro_scope:
            macro = macro_scope[func]
            changed = macro(self, variable_scope, macro_scope)
            return changed.bind(variable_scope, macro_scope)
        return ListExpression(
            expr.bind(variable_scope, macro_scope)
            for expr in self)

    @cached
    def eval(self) -> ValueType:
        func, *args = self
        func = func.eval()
        res = func(args)
        return res


class Function:

    def __init__(self, params: List[str], body: Expression, name: Optional[str] = None):
        self._params = params
        self._body = body
        self._name = name if name is not None else "(anonymous)"

    def __call__(self, args: List[Expression]):
        if len(args) != len(self._params):
            raise TypeError(f"")
        params: Scope[Expression] = Scope()
        for param, arg in zip(self._params, args):
            params[param] = arg
        body = self._body.bind(params, Scope[MacroFunctionType]())
        return body.eval()
