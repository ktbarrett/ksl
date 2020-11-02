import pytest
import textwrap
import ksl.parser as parser
from ksl.parser import parse
import ksl.engine as engine


def test_name():

    test_str = " Jeremy"
    a = parse(test_str)

    assert isinstance(a, engine.Name)
    assert a == "Jeremy"


def test_literal():

    test_str = """  ' wowo "
    asjasd \\\'\\\" '"""
    a = parse(test_str)

    assert isinstance(a, engine.Literal)
    assert a == """ wowo "
    asjasd '" """


def test_unterminated_literal():

    test_str = " \"testing failure"

    with pytest.raises(parser.ParseError):
        parse(test_str)


def test_list_expression():

    test_str = " ( jej (+ '1' '2'))"
    a = parse(test_str)

    assert isinstance(a, engine.ListExpression)
    assert isinstance(a[0], engine.Name) and a[0] == "jej"
    assert isinstance(a[1], engine.ListExpression)
    assert isinstance(a[1][0], engine.Name) and a[1][0] == "+"
    assert isinstance(a[1][1], engine.Literal) and a[1][1] == '1'
    assert isinstance(a[1][2], engine.Literal) and a[1][2] == '2'


def test_unterminated_list_expression():

    test_str = " ( test"

    with pytest.raises(parser.ParseError):
        parse(test_str)


def test_extra_list_terminator():

    test_str = "( yes)) "

    with pytest.raises(parser.ParseError):
        parse(test_str)


def test_bad_toplevel():

    with pytest.raises(parser.ParseError):
        parse(" 1  2")

    with pytest.raises(parser.ParseError):
        parse("   ")


def test_parser_empty():

    with pytest.raises(ValueError):
        parse()


def test_parser_error():

    test_str = textwrap.dedent("""
    (
      1 2""")

    with pytest.raises(parser.ParseError) as err:
        parse(test_str, "lol.ksl")
        assert str(err).startswith("lol.ksl:3:6")


def test_parser_file(tmpdir):

    tmpfile = str(tmpdir.join("temp"))
    test_str = "(+ 1 2)\n"

    with open(tmpfile, "w") as file:
        file.write(test_str)

    a = parse(filename=tmpfile)

    assert isinstance(a, engine.ListExpression)
    assert isinstance(a[0], engine.Name) and a[0] == '+'
    assert isinstance(a[1], engine.Name) and a[1] == '1'
    assert isinstance(a[2], engine.Name) and a[2] == '2'
