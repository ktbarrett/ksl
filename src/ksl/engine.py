from typing import Any, Union, Dict, List, TypeVar, Callable, Optional, Iterable, Iterator
from mypy_extensions import VarArg
from abc import ABC, abstractmethod
from typing import MutableMapping, Mapping
from .utils import cached


ValueType = Any

FunctionType = Callable[[VarArg('Expression')], 'ValueType']

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


class Scope(MutableMapping[str, T]):

    def __init__(self, parent: Union[None, Mapping[str, T]] = None):
        self._scope: Dict[str, T] = {}
        self._parent = parent

    def __getitem__(self, item: str) -> T:
        if item in self._scope:
            return self._scope[item]
        elif self._parent is not None:
            return self._parent[item]
        else:
            raise KeyError(repr(item))

    def __setitem__(self, item: str, value: T) -> None:
        self._scope[item] = value

    def __delitem__(self, item: str) -> None:
        raise NotImplementedError("Scopes do not support removing elements")  # pragma: no cover

    def __iter__(self) -> Iterator[str]:
        yield from self._scope
        if self._parent is not None:
            for name in self._parent:
                if name not in self._scope:
                    yield name

    def __len__(self) -> int:
        return sum(1 for _ in self)


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

    def __repr__(self):
        return repr(self._value)


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
        raise RuntimeError(f"Attempted evaluating unbound name: {self}")


class ListExpression(tuple, Expression):
    _info: Dict[str, Any]

    def __new__(cls, sub_expressions: Iterable[Expression], **info: Any):
        s = tuple.__new__(cls, sub_expressions)
        s._info = info
        return s

    @property
    def info(self) -> Dict[str, Any]:
        return self._info  # pragma: no cover

    def __repr__(self) -> str:
        return '(' + ' '.join(repr(elem) for elem in self) + ')'

    def bind(self, variable_scope: Scope[Expression], macro_scope: Scope[MacroFunctionType]) -> Expression:
        func = self[0]
        new_var_scope = Scope(variable_scope)
        new_macro_scope = Scope(macro_scope)
        if isinstance(func, Name) and func in new_macro_scope:
            macro = new_macro_scope[func]
            changed = macro(self, new_var_scope, new_macro_scope)
            return changed.bind(new_var_scope, new_macro_scope)
        return ListExpression(
            expr.bind(new_var_scope, new_macro_scope)
            for expr in self)

    @cached
    def eval(self) -> ValueType:
        func, *args = self
        func = func.eval()
        res = func(*args)
        return res


class Function:

    def __init__(self, params: List[str], body: Expression, name: Optional[str] = None):
        self._params = params
        self._body = body
        self._name = name if name is not None else "anonymous"

    def __call__(self, *args: Expression):
        if len(args) != len(self._params):
            raise TypeError(f"{self._name} takes {len(self._params)} arguments, but {len(args)} were given")
        scope: Scope[Expression] = Scope()
        # bind arguments to parameters and resolve
        for param, arg in zip(self._params, args):
            scope[param] = arg
        # bind function name for recursive calls
        scope[self._name] = Literal(self)
        # finish resolving all parameters and recursive calls
        body = self._body.bind(scope, Scope[MacroFunctionType]())
        return body.eval()
