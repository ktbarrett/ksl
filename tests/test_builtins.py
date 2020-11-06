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


def test_define_function():

    src = """
    (do
        (def fib (n) (cond
            (= n 0) 1
            (= n 1) 1
                    (+ (fib (- n 1)) (fib (- n 2)))))
        (fib 21))
    """

    assert run(src) == 10946
