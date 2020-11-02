from typing import Iterable, Optional, Union
from os import PathLike
from itertools import chain
from ast import literal_eval
from .utils import window
from .engine import Expression, ListExpression, Name, Literal


def parse(*, source: Optional[Iterable[str]] = None, filename: Optional[Union[str, PathLike]] = None) -> Expression:
    if source is not None:
        if filename is None:
            filename = "(anonymous)"
        else:
            filename = str(filename)
    elif filename is not None:
        source = open(filename)
    else:
        raise ValueError("Must provide either a source, filename, or both to parser")
    p = Parser(source=source, filename=str(filename))
    return p.parse()


class ParseError(Exception):
    pass


class Parser:

    def __init__(self, source: Iterable[str], filename: str):
        self._filename = filename
        self._lineno = 1
        self._charno = 1
        self._iter = self._iterate(source)
        next(self._iter)  # set first values for prev and curr

    def _iterate(self, source: Iterable[str]):
        for self._prev, self._curr in window(chain((None,), source, (None,)), 2):
            yield self._curr
            if self._curr == '\n':
                self._lineno += 1
                self._charno = 1
            else:
                self._charno += 1

    @property
    def filename(self) -> str:
        return self._filename

    @property
    def lineno(self) -> int:
        return self._lineno

    @property
    def charno(self) -> int:
        return self._charno

    @property
    def curr(self):
        return self._curr

    @property
    def prev(self):
        return self._prev

    def step(self) -> str:
        """ Step to the next character in the input """
        try:
            value = next(self._iter)
        except StopIteration:
            pass
        return value

    @property
    def finished(self):
        return self._curr is None

    def error(self, msg: str) -> None:
        """ Create and raise a ParseError """
        raise ParseError(f"{self.filename}:{self.lineno},{self.charno} | " + msg)

    def parse_whitespace(self) -> None:
        # consume any empty space
        while self.curr is not None and self.curr.isspace():
            self.step()

    def parse(self) -> Expression:
        """ Top level parser entry function for scripts """
        self.parse_whitespace()
        # if end of string the input was just whitespace
        if self.finished:
            self.error(f"Empty top-level expression")
        # parse an expression
        res = self.parse_expr()
        # consume any empty space
        self.parse_whitespace()
        # unexpectedly got something else
        if not self.finished:
            self.error(f"Invalid top-level expression")
        return res

    def parse_expr(self) -> Expression:
        """
        Parses the next expression

        EXPR := ATOM | LIST_EXPR
        """
        self.parse_whitespace()
        # decide how to parse expression, is it a list, an atom, or malformed?
        if self.curr == '(':
            return self.parse_list_expression()
        elif self.curr == ')':
            self.error(f"Unexpected ')'")
        return self.parse_atom()

    def parse_list_expression(self) -> ListExpression:
        """
        Parses the next list expression

        LIST_EXPR := '(' WS* (EXPR WS+)* EXPR? WS* ')'
        """
        self.parse_whitespace()
        # ensure we are at the start of a valid list expression
        if self.curr != '(':
            self.error(f"Expecting '(' to start a list expression; found '{self.curr}' instead")
        start_line = self.lineno
        start_char = self.charno
        # consume '('
        self.step()
        sub_expressions = []
        while True:
            # consume any empty space
            self.parse_whitespace()
            if self.finished:
                self.error(f"List expression starting at {self.filename}:{start_line},{start_char} does not terminate")
            # if ')' the list expression is done, otherwise parse the next thing as a sub expression
            if self.curr == ')':
                break
            else:
                expr = self.parse_expr()
                sub_expressions.append(expr)
        # consume ')'
        self.step()
        # yield a list expression
        return ListExpression(
            sub_expressions,
            filename=self.filename,
            start_line=start_line,
            start_char=start_char,
            end_line=self.lineno,
            end_char=self.charno)

    def parse_atom(self) -> Expression:
        """
        Parses the next atom

        ATOM := LITERAL | NAME
        """
        self.parse_whitespace()
        # decide how to parse atom, is it a quoted literal, a name, or malformed?
        if self.curr in ('\'', '\"'):
            return self.parse_literal()
        elif self.curr in ('(', ')'):
            self.error(f"Unexpected '{self.curr}'")
        return self.parse_name()

    def parse_literal(self) -> Literal:
        """ Parses the next literal """
        self.parse_whitespace()
        # ensure we have a valid literal
        if self.curr not in ('\'', '\"'):
            self.error(f"Expecting ' or \" to start literal; found '{self.curr}' instead")
        start_quote = self.curr
        start_line = self.lineno
        start_char = self.charno
        # consume everything between quotes
        token = [self.curr]
        while True:
            token.append(self.step())
            # if we reach the end of input, the string did not terminate
            if self.finished:
                self.error(f"Literal starting at {self.filename}:{start_line},{start_char} does not terminate")
            # strings end when matching an unescaped quote of the same type that started the literal
            if self.curr == start_quote and self.prev != '\\':
                break
        self.step()
        # try to eval string
        token_str = ''.join(token)
        try:
            value = literal_eval(token_str)
        except Exception:
            self.error(f"Could not parse literal {token_str!r} correctly")
        # yield the literal
        return Literal(
            value,
            filename=self.filename,
            start_line=start_line,
            start_char=start_char,
            end_line=self.lineno,
            end_char=self.charno)

    def parse_name(self) -> Name:
        r"""
        Parses the next name

        NAME := \S+
        """
        self.parse_whitespace()
        # ensure we have a valid name
        if self.curr in ('\'', '\"'):
            self.error(f"Expecting a name; found a literal instead")
        if self.curr in (')', '('):
            self.error(f"Expecting a name; found '{self.curr}' instead")
        start_line = self.lineno
        start_char = self.charno
        # consume name
        token = [self.curr]
        while True:
            self.curr is not None and not self.curr.isspace() and self.curr not in ('(', ')')
            self.step()
            token.append(self.curr)
        # yield a name
        token = ''.join(token)
        return Name(
            token,
            filename=self.filename,
            start_line=start_line,
            start_char=start_char,
            end_line=self.lineno,
            end_char=self.charno)
