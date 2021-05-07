from typing import Any
from io import StringIO
from textwrap import dedent

import pytest

from ksl.lex import Lexer, LexError, TokenType, Token


def simple_test(
    token_type: TokenType,
    lex_method: str,
    src: str,
    expected_capture: str,
    expected_value: Any,
) -> None:
    filepath = "test"
    lexer = Lexer(source=StringIO(src), filepath=filepath)
    lexer._next()
    method = getattr(lexer, lex_method)
    t = method()
    assert t == Token(
        type=token_type,
        filepath=filepath,
        start_lineno=1,
        start_charno=1,
        end_lineno=1,
        end_charno=len(expected_capture) + 1,
        capture=expected_capture,
        value=expected_value,
    )


def test_lex_identifier() -> None:
    def identifier_test(src: str, expected_capture: str) -> None:
        simple_test(
            TokenType.Identifier, "_capture_identifier", src, expected_capture, None
        )

    identifier_test("src", "src")
    identifier_test("src ", "src")
    identifier_test("src)", "src")
    identifier_test("-", "-")
    identifier_test("- ", "-")
    identifier_test("-)", "-")
    identifier_test("-abc", "-abc")
    identifier_test("\\(yes", "\\(yes")
    identifier_test("\\5stuff", "\\5stuff")
    identifier_test("a\\\\b", "a\\\\b")
    with pytest.raises(LexError):
        identifier_test("0ab", "")
    with pytest.raises(LexError):
        identifier_test("a\\notescape", "")
    with pytest.raises(LexError):
        identifier_test("\\notescape", "")
    with pytest.raises(LexError):
        identifier_test("wow\0", "")


def test_lex_hex() -> None:
    def hex_test(src: str, expected_capture: str, expected_value: int) -> None:
        simple_test(
            TokenType.Integer, "_capture_hex", src, expected_capture, expected_value
        )

    hex_test("0x1aF", "0x1aF", 0x1AF)
    hex_test("0x1aF ", "0x1aF", 0x1AF)
    hex_test("0X1aF)", "0X1aF", 0x1AF)
    with pytest.raises(LexError):
        hex_test("0x1ap", "", 0)
    with pytest.raises(LexError):
        hex_test("0XP", "", 0)
    with pytest.raises(LexError):
        hex_test("09", "", 0)
    with pytest.raises(LexError):
        hex_test("w", "", 0)


def test_lex_octal() -> None:
    def octal_test(src: str, expected_capture: str, expected_value: int) -> None:
        simple_test(
            TokenType.Integer, "_capture_octal", src, expected_capture, expected_value
        )

    octal_test("0o174", "0o174", 0o174)
    octal_test("0O174 ", "0O174", 0o174)
    octal_test("0o174`", "0o174", 0o174)
    with pytest.raises(LexError):
        octal_test("7", "", 0)
    with pytest.raises(LexError):
        octal_test("0g", "", 0)
    with pytest.raises(LexError):
        octal_test("0o ", "", 0)
    with pytest.raises(LexError):
        octal_test("0O129", "", 0)


def test_lex_binary() -> None:
    def binary_test(src: str, expected_capture: str, expected_value: int) -> None:
        simple_test(
            TokenType.Integer, "_capture_binary", src, expected_capture, expected_value
        )

    binary_test("0b10", "0b10", 0b10)
    binary_test("0b10 ", "0b10", 0b10)
    binary_test("0b10)", "0b10", 0b10)
    with pytest.raises(LexError):
        binary_test("8", "", 0)
    with pytest.raises(LexError):
        binary_test("0j", "", 0)
    with pytest.raises(LexError):
        binary_test("0b3", "", 0)
    with pytest.raises(LexError):
        binary_test("0b1~", "", 0)


def test_lex_decimal_int() -> None:
    def int_test(src: str, expected_capture: str, expected_value: int) -> None:
        simple_test(
            TokenType.Integer, "_capture_decimal", src, expected_capture, expected_value
        )

    int_test("067", "067", 67)
    int_test("0\n", "0", 0)
    int_test("67:", "67", 67)
    int_test("-0 ", "-0", 0)
    with pytest.raises(LexError):
        int_test("f", "", 0)
    with pytest.raises(LexError):
        int_test("-0f", "", 0)


def test_lex_decimal_float() -> None:
    def float_test(src: str, expected_capture: str, expected_value: float) -> None:
        simple_test(
            TokenType.Float, "_capture_decimal", src, expected_capture, expected_value
        )

    float_test("11.0", "11.0", 11.0)
    float_test("1.0 ", "1.0", 1.0)
    float_test("1.01;", "1.01", 1.01)
    float_test("1.", "1.", 1.0)
    float_test("1. ", "1.", 1.0)
    float_test("1.;", "1.", 1.0)
    float_test("1e5 ", "1e5", 1e5)
    float_test("1.E32", "1.E32", 1.0e32)
    with pytest.raises(LexError):
        float_test(".89", "", 0)
    with pytest.raises(LexError):
        float_test("-.89", "", 0)
    with pytest.raises(LexError):
        float_test("1e)", "", 0)


def test_lex_string() -> None:
    def string_test(src: str, expected_capture: str, expected_value: str) -> None:
        simple_test(
            TokenType.String, "_capture_string", src, expected_capture, expected_value
        )

    string_test("'wew' ", "'wew'", "wew")
    string_test("'wew'", "'wew'", "wew")
    string_test('"wew\\n")', '"wew\\n"', "wew\n")
    with pytest.raises(LexError):
        string_test("'does not terminate", "", "")
    with pytest.raises(LexError):
        string_test("not a string", "", "")
    with pytest.raises(LexError):
        string_test(r"'invalid \escape'", "", "")

    def multilinestring_test(
        src: str,
        expected_capture: str,
        expected_value: str,
        expected_end_lineno: int,
        expected_end_charno: int,
    ) -> None:
        lexer = Lexer(source=StringIO(src), filepath="test")
        lexer._next()
        t = lexer._capture_string()
        assert t == Token(
            type=TokenType.String,
            filepath="test",
            start_lineno=1,
            start_charno=1,
            end_lineno=expected_end_lineno,
            end_charno=expected_end_charno,
            capture=expected_capture,
            value=expected_value,
        )

    multilinestring_test(
        "'wew\nlad' ",
        "'wew\nlad'",
        "wew\nlad",
        2,
        5,
    )
    with pytest.raises(LexError):
        multilinestring_test("'wew\nlad ", "", "", 0, 0)


def test_lex_comment() -> None:
    def comment_test(src: str, expected_capture: str) -> None:
        simple_test(TokenType.Comment, "_capture_comment", src, expected_capture, None)

    comment_test("#comment", "#comment")
    comment_test("#comment\n", "#comment")
    comment_test("#comment\\n", "#comment\\n")
    comment_test("#comment\\#more", "#comment\\#")
    with pytest.raises(LexError):
        comment_test("not a comment", "")


def test_indentation() -> None:
    def indentation_test(src: str, expected_capture: str, lineno: int) -> None:
        filepath = "test"
        lexer = Lexer(source=StringIO(src), filepath=filepath)
        lexer._next()
        t = lexer._capture_indentation()
        assert t == Token(
            type=TokenType.Indentation,
            filepath=filepath,
            start_lineno=lineno,
            start_charno=1,
            end_lineno=lineno,
            end_charno=len(expected_capture) + 1,
            capture=expected_capture,
            value=None,
        )

    def end_test(src: str, lineno: int, charno: int) -> None:
        filepath = "test"
        lexer = Lexer(source=StringIO(src), filepath=filepath)
        lexer._next()
        t = lexer._capture_indentation()
        assert t == Token(
            type=TokenType.End,
            filepath=filepath,
            start_lineno=lineno,
            start_charno=charno,
            end_lineno=lineno,
            end_charno=charno,
            capture="",
            value=None,
        )

    end_test("", 1, 1)
    end_test("  ", 1, 3)
    end_test("\n\n", 3, 1)
    end_test("\n\n  ", 3, 3)

    indentation_test("abc", "", 1)
    indentation_test("  (", "  ", 1)
    indentation_test("\n\n;", "", 3)
    indentation_test("\n  9", "  ", 2)
    with pytest.raises(LexError):
        indentation_test("  \n\t(", "", 0)


def test_program() -> None:

    src = dedent(
        """
    (-abc  + 01 ) # no way
        "wow" 'no
    way'

    -0.78e2 0x1f 0b10 0O77
      #inner\\# 67
    {}[:]`,;
    """
    )
    filepath = "test"

    expected = [
        Token(TokenType.Indentation, filepath, 2, 1, 2, 1, "", None),
        Token(TokenType.ListStart, filepath, 2, 1, 2, 2, "(", None),
        Token(TokenType.Identifier, filepath, 2, 2, 2, 6, "-abc", None),
        Token(TokenType.Identifier, filepath, 2, 8, 2, 9, "+", None),
        Token(TokenType.Integer, filepath, 2, 10, 2, 12, "01", 1),
        Token(TokenType.ListEnd, filepath, 2, 13, 2, 14, ")", None),
        Token(TokenType.Comment, filepath, 2, 15, 2, 23, "# no way", None),
        Token(TokenType.Indentation, filepath, 3, 1, 3, 5, "    ", None),
        Token(TokenType.String, filepath, 3, 5, 3, 10, '"wow"', "wow"),
        Token(TokenType.String, filepath, 3, 11, 4, 5, "'no\nway'", "no\nway"),
        Token(TokenType.Indentation, filepath, 6, 1, 6, 1, "", None),
        Token(TokenType.Float, filepath, 6, 1, 6, 8, "-0.78e2", -0.78e2),
        Token(TokenType.Integer, filepath, 6, 9, 6, 13, "0x1f", 0x1F),
        Token(TokenType.Integer, filepath, 6, 14, 6, 18, "0b10", 0b10),
        Token(TokenType.Integer, filepath, 6, 19, 6, 23, "0O77", 0o77),
        Token(TokenType.Indentation, filepath, 7, 1, 7, 3, "  ", None),
        Token(TokenType.Comment, filepath, 7, 3, 7, 11, "#inner\\#", None),
        Token(TokenType.Integer, filepath, 7, 12, 7, 14, "67", 67),
        Token(TokenType.Indentation, filepath, 8, 1, 8, 1, "", None),
        Token(TokenType.SetStart, filepath, 8, 1, 8, 2, "{", None),
        Token(TokenType.SetEnd, filepath, 8, 2, 8, 3, "}", None),
        Token(TokenType.MapStart, filepath, 8, 3, 8, 4, "[", None),
        Token(TokenType.MapSep, filepath, 8, 4, 8, 5, ":", None),
        Token(TokenType.MapEnd, filepath, 8, 5, 8, 6, "]", None),
        Token(TokenType.Tick, filepath, 8, 6, 8, 7, "`", None),
        Token(TokenType.Comma, filepath, 8, 7, 8, 8, ",", None),
        Token(TokenType.Semicolon, filepath, 8, 8, 8, 9, ";", None),
        Token(TokenType.End, filepath, 9, 1, 9, 1, "", None),
    ]

    actual = list(Lexer(source=StringIO(src), filepath=filepath))

    assert actual == expected


def test_end_during_line() -> None:

    src = "123"
    filepath = "test"

    expected = [
        Token(TokenType.Indentation, filepath, 1, 1, 1, 1, "", None),
        Token(TokenType.Integer, filepath, 1, 1, 1, 4, "123", 123),
        Token(TokenType.End, filepath, 1, 4, 1, 4, "", None),
    ]

    actual = list(Lexer(source=StringIO(src), filepath=filepath))

    assert actual == expected


def test_end_during_peek() -> None:

    src = "0"
    filepath = "test"

    expected = [
        Token(TokenType.Indentation, filepath, 1, 1, 1, 1, "", None),
        Token(TokenType.Integer, filepath, 1, 1, 1, 2, "0", 0),
        Token(TokenType.End, filepath, 1, 2, 1, 2, "", None),
    ]

    actual = list(Lexer(source=StringIO(src), filepath=filepath))

    assert actual == expected


def test_unexpected_character() -> None:

    src = "123 \0"
    filepath = "test"

    with pytest.raises(LexError):
        list(Lexer(source=StringIO(src), filepath=filepath))
