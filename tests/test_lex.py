from io import StringIO
from textwrap import dedent
from typing import Any

import pytest

from ksl.lex import Lexer, LexError
from ksl.tokens import Token, TokenType


def simple_test(
    token_type: TokenType,
    lex_method: str,
    src: str,
    expected_value: Any,
) -> None:
    """Returns the first token"""
    filepath = "test"
    lexer = Lexer(source=StringIO(src), path=filepath)
    lexer.next()  # skips nodent
    t = lexer.next()
    assert t == Token(type=token_type, value=expected_value)


def test_lex_identifier() -> None:
    def identifier_test(src: str, expected_value: str) -> None:
        simple_test(TokenType.Identifier, "_capture_identifier", src, expected_value)

    identifier_test("src", "src")
    identifier_test("src ", "src")
    identifier_test("src)", "src")
    identifier_test("-", "-")
    identifier_test("- ", "-")
    identifier_test("-)", "-")
    identifier_test("-abc", "-abc")
    identifier_test("\\(yes", "(yes")
    identifier_test("\\5stuff", "5stuff")
    identifier_test("a\\\\b", "a\\b")
    with pytest.raises(LexError):
        identifier_test("wow\0", "")


def test_lex_int_hex() -> None:
    def hex_test(src: str, expected_value: int) -> None:
        simple_test(TokenType.Integer, "_capture_hex", src, expected_value)

    hex_test("0x1aF", 0x1AF)
    hex_test("0x1aF ", 0x1AF)
    hex_test("0X1aF)", 0x1AF)
    with pytest.raises(LexError):
        hex_test("0x1ap", 0)
    with pytest.raises(LexError):
        hex_test("0XP", 0)


def test_lex_int_octal() -> None:
    def octal_test(src: str, expected_value: int) -> None:
        simple_test(TokenType.Integer, "_capture_octal", src, expected_value)

    octal_test("0o174", 0o174)
    octal_test("0O174 ", 0o174)
    octal_test("0o174`", 0o174)
    with pytest.raises(LexError):
        octal_test("0g", 0)
    with pytest.raises(LexError):
        octal_test("0o ", 0)
    with pytest.raises(LexError):
        octal_test("0O129", 0)


def test_lex_int_binary() -> None:
    def binary_test(src: str, expected_value: int) -> None:
        simple_test(TokenType.Integer, "_capture_binary", src, expected_value)

    binary_test("0b10", 0b10)
    binary_test("0b10 ", 0b10)
    binary_test("0b10)", 0b10)
    with pytest.raises(LexError):
        binary_test("0j", 0)
    with pytest.raises(LexError):
        binary_test("0b", 0)
    with pytest.raises(LexError):
        binary_test("0b1~", 0)


def test_lex_int_decimal() -> None:
    def int_test(src: str, expected_value: int) -> None:
        simple_test(TokenType.Integer, "_capture_number", src, expected_value)

    int_test("067", 67)
    int_test("0\n", 0)
    int_test("67:", 67)
    int_test("-0 ", 0)
    with pytest.raises(LexError):
        int_test("-0f", 0)


def test_lex_float() -> None:
    def float_test(src: str, expected_value: float) -> None:
        simple_test(TokenType.Float, "_capture_number", src, expected_value)

    float_test("11.0", 11.0)
    float_test("1.0 ", 1.0)
    float_test("1.01;", 1.01)
    float_test("1.", 1.0)
    float_test("1. ", 1.0)
    float_test("1.;", 1.0)
    float_test("1e5 ", 1e5)
    float_test("1.E32", 1.0e32)
    with pytest.raises(LexError):
        float_test(".89", 0)
    with pytest.raises(LexError):
        float_test("-.89", 0)
    with pytest.raises(LexError):
        float_test("1e)", 0)


def test_lex_string() -> None:
    def string_test(src: str, expected_value: str) -> None:
        simple_test(TokenType.String, "_capture_string", src, expected_value)

    string_test("'wew' ", "wew")
    string_test("'wew'", "wew")
    string_test('"wew\\n")', "wew\n")
    string_test("'wew\nlad' ", "wew\nlad")
    with pytest.raises(LexError):
        string_test("'does not terminate", "")
    with pytest.raises(LexError):
        string_test(r"'invalid \escape'", "")
    with pytest.raises(LexError):
        string_test("'wew\nlad ", "")


def test_lex_program() -> None:

    src = dedent(
        """
        ()[]{}:`,;
            0b10 0o51 0Xa8
            # comment
        12 -12 -12.01 -12e3
        -12.01e30 12. 12.E30
        0 -0
          -
            --wow abc
        "wow"
        """
    )
    filepath = "test"

    expected = [
        Token(type=TokenType.Nodent),
        Token(type=TokenType.LParen),
        Token(type=TokenType.RParen),
        Token(type=TokenType.LBracket),
        Token(type=TokenType.RBracket),
        Token(type=TokenType.LCurly),
        Token(type=TokenType.RCurly),
        Token(type=TokenType.Colon),
        Token(type=TokenType.Tick),
        Token(type=TokenType.Comma),
        Token(type=TokenType.Semicolon),
        Token(type=TokenType.Indent),
        Token(type=TokenType.Integer, value=0b10),
        Token(type=TokenType.Integer, value=0o51),
        Token(type=TokenType.Integer, value=0xA8),
        Token(type=TokenType.Dedent),
        Token(type=TokenType.Integer, value=12),
        Token(type=TokenType.Integer, value=-12),
        Token(type=TokenType.Float, value=-12.01),
        Token(type=TokenType.Float, value=-12e3),
        Token(type=TokenType.Nodent),
        Token(type=TokenType.Float, value=-12.01e30),
        Token(type=TokenType.Float, value=12.0),
        Token(type=TokenType.Float, value=12.0e30),
        Token(type=TokenType.Nodent),
        Token(type=TokenType.Integer, value=0),
        Token(type=TokenType.Integer, value=-0),
        Token(type=TokenType.Indent),
        Token(type=TokenType.Identifier, value="-"),
        Token(type=TokenType.Indent),
        Token(type=TokenType.Identifier, value="--wow"),
        Token(type=TokenType.Identifier, value="abc"),
        Token(type=TokenType.Dedent),
        Token(type=TokenType.Dedent),
        Token(type=TokenType.String, value="wow"),
    ]

    actual = list(Lexer(source=src, path=filepath))

    assert actual == expected


def test_lexer_unexpected_char():
    with pytest.raises(LexError):
        list(Lexer(source="\0", path=""))


def test_lexer_bad_indentation() -> None:
    with pytest.raises(LexError):
        list(Lexer(source="  a\n\tb", path=""))
    with pytest.raises(LexError):
        list(Lexer(source=" \tstuff", path=""))


def test_lexer_peek_at_end() -> None:
    actuals = list(Lexer(source="0", path=""))
    expecteds = [Token(type=TokenType.Nodent), Token(type=TokenType.Integer, value=0)]
    assert expecteds == actuals


def test_lexer_token_iter() -> None:
    lexer = Lexer(source="123 abc", path="")
    assert lexer.next() == Token(type=TokenType.Nodent)
    assert lexer.next() == Token(type=TokenType.Integer, value=123)
    assert lexer.peek() == Token(type=TokenType.Identifier, value="abc")
    assert lexer.peek(2) == Token(type=TokenType.End)
    assert lexer.next() == Token(type=TokenType.Identifier, value="abc")
    assert lexer.next() == Token(type=TokenType.End)
    assert lexer.next() == Token(type=TokenType.End)
