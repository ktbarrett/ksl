"""
Contains types for the LISP engine.

Since we can easily use Python's types here, this is mostly empty.
There is a function type only because defining Python functions at runtime
is more work than using a simple wrapper object.
"""
from typing import List, Callable, Any


ValueType = Any

FunctionType = Callable[[List['Expression']], ValueType]

MacroFunctionType = Callable[['ListExpression'], 'Expression']


from .engine import Expression, ListExpression  # noqa: E402


class Function:

    def __init__(self, params: List[str], body: Expression):
        self._params = params
        self._body = body

    def __call__(self, args: List[Expression]):
        pass
