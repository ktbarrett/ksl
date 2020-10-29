from typing import Any
from ksl import Eval, Print
from ksl import Scope
from ksl import Expression, Literal, Name, ListExpression
from ksl import LazyValue, LazyLiteral, LazyFunctionCall


def test_literal():

    expr = Literal(value=1)

    assert Eval(expr) == 1
    assert Print(expr) == '1'


def test_lazy_literal():

    lazy_literal = LazyLiteral(value="example")
    assert lazy_literal.value() == "example"


def test_lazy_function_call():

    def add(a: LazyValue, b: LazyValue) -> Any:
        a = a.value()
        b = b.value()
        return a + b

    lazy_eval = LazyFunctionCall(LazyLiteral(value=add), (LazyLiteral(value=1), LazyLiteral(value=2)))
    assert lazy_eval.value() == 3


def test_name():

    expr = Name(name="a")
    scope = Scope()
    scope["a"] = LazyLiteral(value=1)
    assert Eval(expr, scope) == 1


def test_list_expression():

    def add(a: LazyValue, b: LazyValue) -> Any:
        a = a.value()
        b = b.value()
        return a + b

    expr = ListExpression([
        Name(name="add"),
        Literal(value=3),
        Literal(value=2)])

    scope = Scope()
    scope["add"] = LazyLiteral(value=add)

    assert Eval(expr, scope) == 5
