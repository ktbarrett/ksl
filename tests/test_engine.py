from typing import Any
from ksl.engine import Eval, Print
from ksl.engine import Scope
from ksl.engine import Expression, Literal, Name, ListExpression
from ksl.engine import LazyValue, LazyLiteral, LazyFunctionCall


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


def test_nested_expression():

    def add(a: LazyValue, b: LazyValue) -> Any:
        a = a.value()
        b = b.value()
        return a + b

    scope = Scope()
    scope['+'] = LazyLiteral(value=add)

    expr = ListExpression([
        Name('+'),
        Literal(1),
        ListExpression([
            Name('+'),
            Literal(2),
            Literal(3)])])

    assert Eval(expr, scope) == 6
