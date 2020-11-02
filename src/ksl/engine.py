from typing import Any, Union, Protocol, Dict, List, TypeVar, Callable
from .utils import cached


MacroFunctionType = Callable[['ListExpression'], 'Expression']


def eval(expr: 'Expression') -> Any:
    from .builtins import builtin_variables, builtin_macros
    return expr.bind(Scope(builtin_variables), Scope(builtin_macros)).eval()


class Expression(Protocol):

    def bind(self, variable_scope: 'Scope[Expression]', macro_scope: 'Scope[MacroFunctionType]') -> 'Expression':
        pass

    def eval(self) -> Any:
        pass


T = TypeVar('T')


class Scope(Dict[str, T]):

    def __init__(self, parent: Union[None, 'Dict[str, T]'] = None):
        super().__init__()
        self._parent = parent

    @property
    def parent(self) -> Union[None, 'Dict[str, T]']:
        return self._parent

    def __getitem__(self, item: str) -> T:
        if item in self:
            return self[item]
        elif self._parent is not None:
            return self._parent[item]
        return super().__getitem__(item)


class Literal(str, Expression):

    def __new__(cls, value: str, **info: Any):
        s = str.__new__(cls, value)
        s._info = info
        return s

    @property
    def info(self) -> Dict[str, Any]:
        return self._info

    def bind(self, variable_scope: Scope[Expression], macro_scope: Scope[MacroFunctionType]) -> Expression:
        return self

    def eval(self) -> Any:
        return self


class Name(str, Expression):

    def __new__(cls, name: str, **info: Any):
        s = str.__new__(cls, name)
        s._info = info
        return s

    @property
    def info(self) -> Dict[str, Any]:
        return self._info

    def bind(self, variable_scope: Scope[Expression], macro_scope: Scope[MacroFunctionType]) -> Expression:
        return variable_scope[self]

    def eval(self) -> Any:
        raise RuntimeError("Attempted evaluating unbound name")


class Parameter(Name):

    def set_value(self, value: Any) -> None:
        self._value = value

    def eval(self) -> Any:
        return self._value


class ListExpression(tuple, Expression):

    def __new__(cls, sub_expressions: List[Expression], **info: Any):
        s = tuple._new__(cls, sub_expressions)
        s._info = info
        return s

    @property
    def info(self) -> Dict[str, Any]:
        return self._info

    def bind(self, variable_scope: Scope[Expression], macro_scope: Scope[MacroFunctionType]) -> Expression:
        if len(self) >= 1:
            func = self[0]
            if isinstance(func, Name) and func in macro_scope:
                macro = macro_scope[func]
                changed = macro(self)
                return changed.bind(variable_scope, macro_scope)
        for i, expr in enumerate(self):
            self[i] = expr.bind(variable_scope, macro_scope)
        return self

    @cached
    def eval(self) -> Any:
        if len(self) < 1:
            return None
        func, *args = self
        func = func.eval()
        res = func(args)
        return res
