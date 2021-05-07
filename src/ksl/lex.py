from typing import Optional, Any, TextIO, Union, Iterator, List
from dataclasses import dataclass
from ast import literal_eval
from enum import Enum, auto
import os


class TokenType(Enum):
    Indentation = auto()
    Identifier = auto()
    Integer = auto()
    Float = auto()
    String = auto()
    Comment = auto()
    ListStart = auto()
    ListEnd = auto()
    SetStart = auto()
    SetEnd = auto()
    MapStart = auto()
    MapEnd = auto()
    MapSep = auto()
    Comma = auto()
    Semicolon = auto()
    Tick = auto()
    End = auto()


@dataclass(frozen=True)
class Token:
    type: TokenType
    filepath: Union["os.PathLike[str]", str]
    start_lineno: int
    start_charno: int
    end_lineno: int
    end_charno: int
    capture: str
    value: Optional[Any] = None


@dataclass
class LexError(Exception):
    filepath: Union["os.PathLike[str]", str]
    start_lineno: int
    start_charno: int
    end_lineno: int
    end_charno: int
    msg: str

    def __post_init__(self) -> None:
        super().__init__(self.msg)


class LexState(Enum):
    START = 0
    RUNNING = 1
    FINISHED = 2


class Lexer:
    filepath: Union["os.PathLike[str]", str]
    lineno: int
    charno: int
    indentation_char: Optional[str]

    def __init__(self, *, source: TextIO, filepath: Union["os.PathLike[str]", str]):
        self._src_it = iter(lambda: source.read(1), "")
        self._state = LexState.START
        self._curr: str = ""
        self._lookahead: Optional[str] = None
        self._start_lineno: int
        self._start_charno: int
        self._capture: Optional[List[str]] = None
        self.filepath = filepath
        self.lineno = 1
        self.charno = 1
        self.indentation_char = None

    def _next(self) -> None:
        # increment lineno and charno
        if self._curr == "":
            # don't increment if at beginning or end of file
            pass
        elif self._curr == "\n":
            self.lineno += 1
            self.charno = 1
        else:
            self.charno += 1
        # save current character to buffer if capturing
        if self._capture is not None:
            self._capture.append(self._curr)
        # get next value in input stream
        if self._lookahead is not None:
            self._curr, self._lookahead = self._lookahead, None
        else:
            try:
                self._curr = next(self._src_it)
            except StopIteration:
                self._curr = ""

    def _peek(self) -> str:
        if self._lookahead is not None:
            return self._lookahead
        try:
            self._lookahead = next(self._src_it)
        except StopIteration:
            self._lookahead = ""
        return self._lookahead

    def _start_capture(self) -> None:
        assert self._capture is None
        self._capture = []
        self._start_lineno = self.lineno
        self._start_charno = self.charno

    def _abandon_capture(self) -> None:
        assert self._capture is not None
        self._capture = None

    def _finish_capture(
        self, token_type: TokenType, *, value: Optional[Any] = None
    ) -> Token:
        assert self._capture is not None
        res = Token(
            type=token_type,
            filepath=self.filepath,
            start_lineno=self._start_lineno,
            start_charno=self._start_charno,
            end_lineno=self.lineno,
            end_charno=self.charno,
            capture=self._get_capture(),
            value=value,
        )
        self._capture = None
        return res

    def _error_capture(self, msg: str) -> LexError:
        assert self._capture is not None
        res = LexError(
            msg=msg,
            filepath=self.filepath,
            start_lineno=self._start_lineno,
            start_charno=self._start_charno,
            end_lineno=self.lineno,
            end_charno=self.charno,
        )
        self._capture = None
        return res

    def _get_capture(self) -> str:
        assert self._capture is not None
        return "".join(self._capture)

    _whitespace = frozenset(" \t")
    _separators = frozenset(")]}#,;:`") | _whitespace | frozenset(("", "\n"))
    _digits = frozenset("0123456789")
    _hex_chars = frozenset("0123456789abcdefABCDEF")
    _octal_chars = frozenset("01234567")
    _binary_chars = frozenset("01")
    _string_escapes = frozenset("abfnrtv\\'\"")
    _identifier_start_chars = frozenset(
        "~!@$%^&*-_=+|<.>/?abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    )
    _identifier_rest_chars = _identifier_start_chars | _digits
    _identifier_rest_escapes = frozenset("`#()\\[{]};:'\",")
    _identifier_start_escapes = frozenset("`#()\\[{]};:'\",") | _digits

    def __iter__(self) -> Iterator[Token]:
        return self

    def __next__(self) -> Token:
        if self._state == LexState.RUNNING:

            while self._curr in self._whitespace:
                self._next()

            if self._curr == "\n":
                self._next()
                return self._capture_indentation()

            elif self._curr in ("'", '"'):
                return self._capture_string()

            elif self._curr == "#":
                return self._capture_comment()

            elif self._curr == "-":
                if self._peek() in self._digits:
                    return self._capture_decimal()
                else:
                    return self._capture_identifier()

            elif self._curr == "0":
                if self._peek() in ("x", "X"):
                    return self._capture_hex()
                elif self._peek() in ("o", "O"):
                    return self._capture_octal()
                elif self._peek() in ("b", "B"):
                    return self._capture_binary()
                else:
                    return self._capture_decimal()

            elif self._curr in self._digits:
                return self._capture_decimal()

            elif self._curr in self._identifier_start_chars or self._curr == "\\":
                return self._capture_identifier()

            elif self._curr == "(":
                self._start_capture()
                self._next()
                return self._finish_capture(TokenType.ListStart)

            elif self._curr == ")":
                self._start_capture()
                self._next()
                return self._finish_capture(TokenType.ListEnd)

            elif self._curr == "{":
                self._start_capture()
                self._next()
                return self._finish_capture(TokenType.SetStart)

            elif self._curr == "}":
                self._start_capture()
                self._next()
                return self._finish_capture(TokenType.SetEnd)

            elif self._curr == "[":
                self._start_capture()
                self._next()
                return self._finish_capture(TokenType.MapStart)

            elif self._curr == "]":
                self._start_capture()
                self._next()
                return self._finish_capture(TokenType.MapEnd)

            elif self._curr == ":":
                self._start_capture()
                self._next()
                return self._finish_capture(TokenType.MapSep)

            elif self._curr == "`":
                self._start_capture()
                self._next()
                return self._finish_capture(TokenType.Tick)

            elif self._curr == ",":
                self._start_capture()
                self._next()
                return self._finish_capture(TokenType.Comma)

            elif self._curr == ";":
                self._start_capture()
                self._next()
                return self._finish_capture(TokenType.Semicolon)

            elif self._curr == "":
                self._state = LexState.FINISHED
                self._start_capture()
                return self._finish_capture(TokenType.End)

            self._start_capture()
            self._next()
            raise self._error_capture(f"unexpected character {self._curr!r}")

        elif self._state == LexState.START:
            self._state = LexState.RUNNING
            self._next()
            return self._capture_indentation()

        # we are in the FINISH state, close the iterator
        raise StopIteration

    def _capture_indentation(self) -> Token:
        self._start_capture()
        while True:
            if self._curr == self.indentation_char:
                self._next()
            elif self._curr == "\n":
                self._abandon_capture()
                self._next()
                self._start_capture()
            elif self._curr == "":
                self._abandon_capture()
                self._start_capture()
                self._state = LexState.FINISHED
                return self._finish_capture(TokenType.End)
            elif self._curr not in self._whitespace:
                return self._finish_capture(TokenType.Indentation)
            elif self.indentation_char is None:
                self.indentation_char = self._curr
                self._next()
            else:
                raise self._error_capture("mixing indentation characters")

    def _capture_string(self) -> Token:
        self._start_capture()
        if self._curr not in ("'", '"'):
            raise self._error_capture("expected string delimiter")
        string_delimiter = self._curr
        self._next()
        while True:
            if self._curr == string_delimiter:
                self._next()
                xtra = string_delimiter * 2
                value = literal_eval(f"{xtra}{self._get_capture()}{xtra}")
                return self._finish_capture(TokenType.String, value=value)
            elif self._curr == "\\":
                self._next()
                if self._curr not in self._string_escapes:
                    raise self._error_capture("invalid escape sequence")
                self._next()
            elif self._curr == "":
                # end of stream without closing string is an error
                raise self._error_capture("unterminated string")
            else:
                self._next()

    def _capture_comment(self) -> Token:
        self._start_capture()
        if not self._curr == "#":
            raise self._error_capture("expecting '#'")
        self._next()
        while True:
            if self._curr == "\n" or self._curr == "":
                return self._finish_capture(TokenType.Comment)
            elif self._curr == "\\":
                self._next()
                if self._curr == "#":
                    self._next()
                    return self._finish_capture(TokenType.Comment)
            else:
                self._next()

    def _capture_identifier(self) -> Token:
        self._start_capture()
        if self._curr == "-":
            self._next()
            # if just the identifier "-"
            if self._curr in self._separators:
                return self._finish_capture(TokenType.Identifier)
        if self._curr in self._identifier_start_chars:
            self._next()
        elif self._curr == "\\":
            self._next()
            if self._curr not in self._identifier_start_escapes:
                raise self._error_capture("invalid escaped identifier start character")
            self._next()
        else:
            raise self._error_capture("invalid identifier start character")
        while True:
            if self._curr in self._identifier_rest_chars:
                self._next()
            elif self._curr in self._separators:
                return self._finish_capture(TokenType.Identifier)
            elif self._curr == "\\":
                self._next()
                if self._curr not in self._identifier_rest_escapes:
                    raise self._error_capture("invalid escaped identifier character")
                self._next()
            else:
                raise self._error_capture("invalid identifier character")

    def _capture_hex(self) -> Token:
        self._start_capture()
        if self._curr != "0":
            raise self._error_capture("invalid hex literal prefix")
        self._next()
        if self._curr not in ("x", "X"):
            raise self._error_capture("invalid hex literal prefix")
        self._next()
        if self._curr not in self._hex_chars:
            raise self._error_capture("expecting hex digit")
        while self._curr in self._hex_chars:
            self._next()
        if self._curr not in self._separators:
            raise self._error_capture("expecting hex digit")
        value = literal_eval(self._get_capture())
        assert isinstance(value, int)
        return self._finish_capture(TokenType.Integer, value=value)

    def _capture_octal(self) -> Token:
        self._start_capture()
        if self._curr != "0":
            raise self._error_capture("invalid octal literal prefix")
        self._next()
        if self._curr not in ("o", "O"):
            raise self._error_capture("invalid octal literal prefix")
        self._next()
        if self._curr not in self._octal_chars:
            raise self._error_capture("expecting octal digit")
        while self._curr in self._octal_chars:
            self._next()
        if self._curr not in self._separators:
            raise self._error_capture("expecting octal digit")
        value = literal_eval(self._get_capture())
        assert isinstance(value, int)
        return self._finish_capture(TokenType.Integer, value=value)

    def _capture_binary(self) -> Token:
        self._start_capture()
        if self._curr != "0":
            raise self._error_capture("invalid binary literal prefix")
        self._next()
        if self._curr not in ("b", "B"):
            raise self._error_capture("invalid binary literal prefix")
        self._next()
        if self._curr not in self._binary_chars:
            raise self._error_capture("expecting binary digit")
        while self._curr in self._binary_chars:
            self._next()
        if self._curr not in self._separators:
            raise self._error_capture("expecting binary digit")
        value = literal_eval(self._get_capture())
        assert isinstance(value, int)
        return self._finish_capture(TokenType.Integer, value=value)

    def _capture_decimal(self) -> Token:
        self._start_capture()
        # capture optional minus
        if self._curr == "-":
            self._next()
        # capture at least one whole digit
        if self._curr not in self._digits:
            raise self._error_capture("invalid digit")
        self._next()
        # consume integer part of the float/integer
        while self._curr in self._digits:
            self._next()
        # if we are done, it's an integer, finish capture and eval literal
        if self._curr in self._separators:
            value = self._parse_int(self._get_capture())
            return self._finish_capture(TokenType.Integer, value=value)
        # consume optional fractional
        if self._curr == ".":
            self._next()
            while self._curr in self._digits:
                self._next()
        # consume optional exponential
        if self._curr in ("e", "E"):
            self._next()
            if self._curr not in self._digits:
                raise self._error_capture("exponent must have at least one digit")
            self._next()
            while self._curr in self._digits:
                self._next()
        # ensure end on separator
        if self._curr not in self._separators:
            raise self._error_capture("invalid digit")
        # finish capture as float, eval literal
        value = literal_eval(self._get_capture())
        assert isinstance(value, float)
        return self._finish_capture(TokenType.Float, value=value)

    @staticmethod
    def _parse_int(capture: str) -> int:
        no_leading_zeros = []
        if capture.startswith("-"):
            no_leading_zeros.append("-")
            no_leading_zeros.append(capture[1:-1].lstrip("0"))
        else:
            no_leading_zeros.append(capture[:-1].lstrip("0"))
        no_leading_zeros.append(capture[-1])
        value = literal_eval("".join(no_leading_zeros))
        assert isinstance(value, int)
        return value


if __name__ == "__main__":  # pragma: no cover
    import sys

    for token in Lexer(source=sys.stdin, filepath="(stdin)"):
        print(token)
