import pytest
from ksl.engine import Scope, Literal, ListExpression, Name, eval as ksleval


def test_literal():

    test_expr = Literal('wew lad')
    r = ksleval(test_expr)
    assert r == 'wew lad'


def test_name_fails():

    test_expr = Name('jeb')

    with pytest.raises(NameError):
        ksleval(test_expr)

    with pytest.raises(RuntimeError):
        test_expr.eval()


def test_name_found():

    env = Scope()
    env['jeb'] = Literal('mess')

    test_expr = Name('jeb')

    r = ksleval(test_expr, env)
    assert r == 'mess'


def test_list_expression():

    env = Scope()
    env['+'] = Literal(lambda args: sum(arg.eval() for arg in args))

    test_expr = ListExpression([
        Name('+'),
        Literal(1),
        Literal(2),
        Literal(3)])

    r = ksleval(test_expr, env)
    assert r == 6


def test_empty_list_expression():

    with pytest.raises(ValueError):
        ListExpression([])
