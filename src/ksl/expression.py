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


class ExpressionList(Value):

    def __init__(self, sub_expressions: List[Value]):
        self._sub_expr = sub_expressions

    def eval(self, scope):
        pass

    def literal(self):
        return "(" + " ".join(expr.literal for expr in self._sub_expr) + ")"


class Integer(Value):

    def __init__(self, value: int):
        self._value = value

    def eval(self, scope):
        return self._value

    def literal(self):
        return repr(self._value)


class Float(Value):

    def __init__(self, value: float):
        self._value = value

    def eval(self, scope):
        return self._value

    def literal(self):
        return repr(self._value)


class String(Value):

    def __init__(self, value: str):
        self._value = value

    def eval(self, scope):
        return self._value

    def literal(self):
        return repr(self._value)
