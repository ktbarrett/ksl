from typing import List
from abc import ABC, abstractmethod


class Value(ABC):

    def __init__(self, lineno: int, charno: int):
        self._lineno = lineno
        self._charno = charno

    @property
    def lineno(self) -> int:
        return self._lineno

    @property
    def charno(self) -> int:
        return self._charno

    @abstractmethod
    def eval(self, scope):
        pass

    @abstractmethod
    def literal(self) -> str:
        pass


class Name(Value):

    def __init__(self, name: str, lineno: int, charno: int):
        super().__init__(lineno, charno)
        self._name = name

    def eval(self, scope):
        return scope[self._name]

    def literal(self):
        return self._name


class ExpressionList(Value):

    def __init__(self, sub_expressions: List[Value], lineno: int, charno: int):
        self._sub_expr = sub_expressions

    def eval(self, scope):
        if not self._sub_expr:
            return None
        func = self._sub_expr[0]
        args = self._sub_expr[1:]
        scope = scope.enter()
        func = func.eval(scope)
        res = func(scope, *args)
        return res

    def literal(self):
        return "(" + " ".join(expr.literal for expr in self._sub_expr) + ")"


class Integer(Value):

    def __init__(self, value: int, lineno: int, charno: int):
        self._value = value

    def eval(self, scope):
        return self._value

    def literal(self):
        return repr(self._value)


class Float(Value):

    def __init__(self, value: float, lineno: int, charno: int):
        self._value = value

    def eval(self, scope):
        return self._value

    def literal(self):
        return repr(self._value)


class String(Value):

    def __init__(self, value: str, lineno: int, charno: int):
        self._value = value

    def eval(self, scope):
        return self._value

    def literal(self):
        return repr(self._value)
