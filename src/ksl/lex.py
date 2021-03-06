from ast import literal_eval
from collections import deque
from io import StringIO
from typing import (
    Any,
    Collection,
    Deque,
    Iterator,
    List,
    Optional,
    TextIO,
    Type,
    Union,
    cast,
)

import ksl.tokens as tokens
from ksl.types import Path


class LexError(Exception):
    pass


class Lexer(Iterator[tokens.Token]):
    indentation: Optional[str]
    curr: tokens.Token
    path: Path
    lineno: int
    charno: int

    START = tokens.Start()
    END = tokens.End()
    _START = "START"
    _END = ""

    def __init__(
        self,
        *,
        source: Union[str, TextIO],
        path: Path,
        indentation: Optional[str] = None,
    ):
        self._source: TextIO
        if source is None:
            self._source = open(path)
        elif isinstance(source, str):
            self._source = StringIO(source)
        else:
            self._source = source
        self.indentation = indentation
        self.curr = self.START
        self.path = path
        self.lineno = 1
        self.charno = 0
        self._lookahead: Deque[tokens.Token] = deque()
        self._indentations = [0]
        self._capture: List[str] = []
        self._curr = self._START
        self._src_lookahead: Deque[str] = deque()

    def peek(self, i: int = 1) -> tokens.Token:
        missing = i - len(self._lookahead)
        while missing > 0:
            self._lex()
            missing = i - len(self._lookahead)
        return self._lookahead[i - 1]

    def next(self) -> tokens.Token:
        if self.curr == self.END:
            return self.curr
        if not self._lookahead:
            self._lex()
        self.curr = self._lookahead.popleft()
        return self.curr

    def __next__(self) -> tokens.Token:
        nxt = self.next()
        if nxt == self.END:
            raise StopIteration
        return nxt

    def _peek(self, i: int = 1) -> str:
        assert i > 0
        missing = i - len(self._src_lookahead)
        if missing > 0:
            self._src_lookahead.extend(self._source.read(missing))
        try:
            return self._src_lookahead[i - 1]
        except IndexError:
            return self._END

    def _next(self) -> str:
        if self._src_lookahead:
            nxt = self._src_lookahead.popleft()
        else:
            nxt = self._source.read(1)
        if nxt == self._END:
            pass
        elif self._curr == "\n":
            self.lineno += 1
            self.charno = 1
        else:
            self.charno += 1
        self._curr = nxt
        return nxt

    def _save(self) -> None:
        self._capture.append(self._curr)

    def _save_and_next(self) -> str:
        self._save()
        return self._next()

    def _assert_save_and_next(self, expected: Union[str, Collection[str]]) -> str:
        if isinstance(expected, str):
            fail = self._curr != expected
        else:
            fail = self._curr not in expected
        if fail:
            raise LexError(
                f"caught unexpected character {self._curr!r}, expecting {expected!r}"
            )
        return self._save_and_next()

    def _reset(self) -> None:
        self._capture.clear()

    def _emit(self, ttype: Type[tokens.Token], value: Optional[Any] = None) -> None:
        self._lookahead.append(ttype(value))

    def _error(self, msg: str) -> LexError:
        return LexError(msg)

    _whitespace = frozenset(" \t")
    _separators = frozenset(")]}#,;:`") | _whitespace | frozenset((_END, "\n"))
    _digits = frozenset("0123456789")
    _hex_chars = frozenset("0123456789abcdefABCDEF")
    _octal_chars = frozenset("01234567")
    _binary_chars = frozenset("01")
    _string_escapes = frozenset("abfnrtv\\'\"")
    _name_chars = (
        frozenset(
            "~!@$%^&*-_=+|<.>/?abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        )
        | _digits
    )

    def _lex(self) -> None:
        while True:
            if self._curr in self._whitespace:
                self._next()
                continue
            if self._curr in ("\n", self._START):
                self._next()
                self._reset()
                while self._curr in self._whitespace:
                    self._save_and_next()
                if self._curr in ("\n", "#", self._END):
                    continue
                if self.indentation is None:
                    if len(self._capture) == 0:
                        return self._emit(tokens.Nodent)
                    if len(set(self._capture)) > 1:
                        raise self._error(
                            "detected indentation is comprised of both spaces and tabs"
                        )
                    self.indentation = "".join(self._capture)
                capture = "".join(self._capture)
                indents = len(capture) // len(self.indentation)
                if capture != (self.indentation * indents):
                    raise self._error("mixing indentation")
                elif indents > self._indentations[-1]:
                    self._indentations.append(indents)
                    return self._emit(tokens.Indent)
                elif indents < self._indentations[-1]:
                    while len(self._capture) < self._indentations[-1]:
                        self._indentations.pop()
                        self._emit(tokens.Dedent)
                    return
                else:
                    return self._emit(tokens.Nodent)
            if self._curr == "#":
                while self._curr != "\n":
                    self._next()
                continue
            if self._curr == "-":
                if self._peek() in self._digits:
                    return self._capture_number()
                else:
                    return self._capture_name()
            if self._curr == "0":
                if self._peek() in ("x", "X"):
                    return self._capture_hex()
                elif self._peek() in ("o", "O"):
                    return self._capture_octal()
                elif self._peek() in ("b", "B"):
                    return self._capture_binary()
                else:
                    return self._capture_number()
            if self._curr in self._digits:
                self._capture_number()
                return
            if self._curr in self._name_chars or self._curr == "\\":
                self._capture_name()
                return
            if self._curr in ('"', "'"):
                return self._capture_string()
            if self._curr == "(":
                self._next()
                return self._emit(tokens.LParen)
            if self._curr == ")":
                self._next()
                return self._emit(tokens.RParen)
            if self._curr == "{":
                self._next()
                return self._emit(tokens.LCurly)
            if self._curr == "}":
                self._next()
                return self._emit(tokens.RCurly)
            if self._curr == "[":
                self._next()
                return self._emit(tokens.LBracket)
            if self._curr == "]":
                self._next()
                return self._emit(tokens.RBracket)
            if self._curr == ":":
                self._next()
                return self._emit(tokens.Colon)
            if self._curr == ",":
                self._next()
                return self._emit(tokens.Comma)
            if self._curr == ";":
                self._next()
                return self._emit(tokens.Semicolon)
            if self._curr == "`":
                self._next()
                return self._emit(tokens.Tick)
            if self._curr == self._END:
                for _ in range(len(self._indentations) - 1):
                    self._indentations.pop()
                    self._emit(tokens.Dedent)
                return self._emit(tokens.End)
            raise self._error(f"unexpected character {self._curr!r}")

    def _capture_name(self) -> None:
        self._reset()
        if self._curr in ("-", "."):
            self._save_and_next()
            if self._curr == ".":
                self._save_and_next()
            if self._curr in self._separators:
                return self._emit(tokens.Name, "".join(self._capture))
        if self._curr in self._digits:
            raise self._error("found number, not name")
        while True:
            if self._curr in self._name_chars:
                self._save_and_next()
            elif self._curr == "\\":
                self._next()
                self._save_and_next()
            elif self._curr in self._separators:
                value = "".join(self._capture)
                return self._emit(tokens.Name, value)
            else:
                raise self._error(f"unexpected name character {self._curr!r}")

    def _capture_string(self) -> None:
        self._reset()
        start_char = self._curr
        self._assert_save_and_next(("'", '"'))
        while self._curr != self._END:
            if self._curr == start_char:
                self._save_and_next()
                value = self._parse_string(self._capture)
                return self._emit(tokens.String, value)
            elif self._curr == "\\":
                self._save_and_next()
                if self._curr not in self._string_escapes:
                    raise self._error(f"Invalid string escape {self._curr}")
                self._save_and_next()
            else:
                self._save_and_next()
        raise self._error("unterminated string")

    def _capture_number(self) -> None:
        self._reset()
        if self._curr == "-":
            self._save_and_next()
        if self._curr not in self._digits:
            raise LexError("number must have at least one digit")
        while self._curr in self._digits:
            self._save_and_next()
        if self._curr in self._separators:
            value = self._parse_int(self._capture)
            return self._emit(tokens.Integer, value)
        if self._curr == ".":
            self._save_and_next()
            while self._curr in self._digits:
                self._save_and_next()
        if self._curr in ("e", "E"):
            self._save_and_next()
            if self._curr in self._digits:
                self._save_and_next()
            else:
                raise self._error("exponent must contain at least one digit")
            while self._curr in self._digits:
                self._save_and_next()
        if self._curr in self._separators:
            value = literal_eval("".join(self._capture))
            return self._emit(tokens.Float, value)
        raise self._error(f"number contained unexpected character {self._curr!r}")

    def _capture_hex(self) -> None:
        self._reset()
        self._assert_save_and_next("0")
        self._assert_save_and_next(("x", "X"))
        while self._curr in self._hex_chars:
            self._save_and_next()
        if len(self._capture) == 2:
            raise self._error("hex literal must have at least one hex digit")
        if self._curr in self._separators:
            value = literal_eval("".join(self._capture))
            return self._emit(tokens.Integer, value)
        raise self._error(f"unexpected character in hex literal {self._curr!r}")

    def _capture_octal(self) -> None:
        self._reset()
        self._assert_save_and_next("0")
        self._assert_save_and_next(("o", "O"))
        while self._curr in self._octal_chars:
            self._save_and_next()
        if len(self._capture) == 2:
            raise self._error("octal literal must have at least one octal digit")
        if self._curr in self._separators:
            value = literal_eval("".join(self._capture))
            return self._emit(tokens.Integer, value)
        raise self._error(f"unexpected character in octal literal {self._curr!r}")

    def _capture_binary(self) -> None:
        self._reset()
        self._assert_save_and_next("0")
        self._assert_save_and_next(("b", "B"))
        while self._curr in self._binary_chars:
            self._save_and_next()
        if self._curr in self._separators:
            if len(self._capture) == 2:
                raise self._error("binary literal must have at least one binary digit")
            value = literal_eval("".join(self._capture))
            return self._emit(tokens.Integer, value)
        raise self._error(f"unexpected character in binary literal {self._curr!r}")

    @staticmethod
    def _parse_string(capture: List[str]) -> str:
        # because strings can cross multiple lines we turn them into Python long strings
        # so literal_eval doesn't complain
        s = capture[0]
        string = "".join(capture)
        return cast(str, literal_eval(f"{s}{s}{string}{s}{s}"))

    @staticmethod
    def _parse_int(capture: List[str]) -> int:
        # skip negative if present
        if capture[0] == "-":
            negative = "-"
            capture = capture[1:]
        else:
            negative = ""
        fixed_string = "".join(
            (negative, "".join(capture[:-1]).lstrip("0"), capture[-1])
        )
        return cast(int, literal_eval(fixed_string))


if __name__ == "__main__":  # pragma: no cover
    import sys

    lexer = Lexer(source=sys.stdin, path="(stdin)")
    for token in lexer:
        print(token)
