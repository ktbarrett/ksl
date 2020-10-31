"""
Contains types for the LISP engine.

Since we can easily use Python's types here, this is mostly empty.
There is a function type only because defining Python functions at runtime
is more work than using a simple wrapper object.
"""
from typing import List, Callable, Any, Union
from .engine import Expression


class Function(Callable[[Expression, ...], Any]):

    def __init__(self, params: List[str], body: Expression):
        self._params = params
        self._body = body

    def __call__(self, *args: Expression):
        pass


ValueType = Union[int, float, str, Callable[[Expression, ...], 'ValueType']]


MacroFunctionType = Callable[[Expression, ...], Expression]
