import pytest
import ksl
from ksl.engine import Scope, Literal, ListExpression, Name, Function
import re


def test_scope():

    s = Scope[int]()
    assert len(s) == 0
    assert "wew" not in s

    s["wew"] = 67
    assert len(s) == 1
    assert "wew" in s

    p = Scope[int](s)
    p["jej"] = 123
    assert len(p) == 2
    assert "wew" in p

    p["wew"] = 1
    assert p["wew"] == 1
    assert len(p) == 2


def test_literal():

    test_expr = Literal('wew lad')
    r = ksl.eval(test_expr)
    assert r == 'wew lad'


def test_name_fails():

    test_expr = Name('jeb')

    with pytest.raises(RuntimeError):
        ksl.eval(test_expr)


def test_name_found():

    env = Scope()
    env['jeb'] = Literal('mess')

    test_expr = Name('jeb')

    r = ksl.eval(test_expr, env)
    assert r == 'mess'


def test_list_expression():

    env = Scope()
    env['+'] = Literal(lambda a, b, c: a.eval() + b.eval() + c.eval())

    test_expr = ListExpression((
        Name('+'),
        Literal(1),
        Literal(2),
        Literal(3)))

    r = ksl.eval(test_expr, env)
    assert r == 6


def test_empty_list_expression():

    with pytest.raises(ValueError):
        ListExpression(())


def test_function():

    params = ['a', 'b']

    body = ListExpression((
        Literal(lambda a, b: a.eval() + b.eval()),
        Name('a'),
        Name('b')))

    func = Literal(Function(params, body, name="add"))

    test_expr = ListExpression((
        Literal(lambda a, b: a.eval() + b.eval()),
        ListExpression((
            func,
            Literal(1),
            Literal(2))),
        ListExpression((
            func,
            Literal(3),
            Literal(4)))))

    r = ksl.eval(test_expr, Scope(), Scope())
    assert r == 10


def test_function_not_enough_args():

    params = ['a', 'b']

    body = ListExpression((
        Literal(lambda a, b: a.eval() + b.eval()),
        Name('a'),
        Name('b')))

    func = Literal(Function(params, body, name="add"))

    test_expr = ListExpression((
        func,
        Literal(5)))

    with pytest.raises(TypeError):
        ksl.eval(test_expr)


def test_function_too_many_args():

    params = ['a', 'b']

    body = ListExpression((
        Literal(lambda a, b: a.eval() + b.eval()),
        Name('a'),
        Name('b')))

    func = Literal(Function(params, body, name="add"))

    test_expr = ListExpression((
        func,
        Literal(5),
        Literal(6),
        Literal('wew')))

    with pytest.raises(TypeError):
        ksl.eval(test_expr)


def test_run():

    e = ListExpression((
        Literal(lambda a, b: a.eval() + b.eval()),
        Literal(1),
        Literal(2)))

    assert ksl.run(e) == 3


def test_repr():

    e = ListExpression((
        Literal(lambda a, b: a.eval() + b.eval()),
        Literal(1),
        Literal(2)))

    assert re.match(r'\(<.*> 1 2\)', repr(e))
