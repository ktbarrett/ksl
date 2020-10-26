from typing import Protocol, List
from .scope import Scope


class Value(Protocol):

    def eval(self, scope: 'Scope') -> 'Value':
        pass

    def literal(self) -> str:
        pass


class Name(Value):

    def __init__(self, name: str):
        self._name = name

    def eval(self, scope):
        return scope[self._name]

    def literal(self):
        return self._name


class Expression(Value):

    def __init__(self, sub_expressions: List[Value]):
        self._sub_expr = sub_expressions

    def eval(self):
        pass

    def literal(self):
        return "(" + " ".join(expr.literal for expr in self._sub_expr) + ")"


class Integer()
