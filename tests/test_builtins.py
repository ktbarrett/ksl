"""
Builds on a correct parser and evaluator
"""
from ksl import run


def test_int():
    assert run("(int '123')") == 123
    assert run("(- (int '98') (int '2'))") == 96


def test_float():
    assert run("(float '123e9')") == 123e9
    assert run("(+ (float '9.8') (float '2.0123'))") == 11.8123


def test_string():
    assert run("(str (int '123'))") == '123'
    assert run("(str (% (int '10') (int '3')))") == '1'


def test_equals():
    assert run("""
        (= (- 2 1) 1)""")


def test_cond():
    assert run("""
        (cond
            (= 0 1) 0
            (= 0 0) 1
            0)""")


def test_define_function():

    src = """
    (do
        (def fib (n) (cond
            (= n 1) 1
            (= n 2) 1
                    (+ (fib (- n 1)) (fib (- n 2)))))
        (fib 5))
    """

    assert run(src) == 5


def test_let_and_scoping():

    assert run("""
        (do
            (let a 5)
            (let b 8)
            (+ a (do
                (let a 3)
                (+ a b))))
        """) == 16


def test_lambda_and_anonymous_name():

    assert run("""
        ((lambda (n) (cond
            (= n 1) 1
            (= n 2) 1
                    (+ (anonymous (- n 1)) (anonymous (- n 2)))))
            5)
        """) == 5
