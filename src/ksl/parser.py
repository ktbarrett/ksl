from typing import Iterable, Optional, Union
from os import PathLike
from itertools import chain
from ast import literal_eval
from .utils import window
from .engine import Expression, ListExpression, Name, Literal


class ParseError(Exception):
    pass


class Parser:

    def __init__(self, *, source: Optional[Iterable[str]] = None, filename: Optional[Union[str, PathLike]] = None):
        if source is not None:
            if filename is None:
                filename = "(anonymous)"
            else:
                filename = str(filename)
        elif filename is not None:
            source = open(filename)
        else:
            raise ValueError("Must provide either a source, filename, or both to lex")

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

    def step(self) -> None:
        """ Step to the next character in the input """
        try:
            return next(self._iter)
        except StopIteration:
            pass

    def error(self, msg: str) -> None:
        """ Create and raise a ParseError """
        raise ParseError(f"{self.filename}:{self.lineno},{self.charno} | " + msg)

    def parse(self) -> Expression:
        """ Top level parser entry function for scripts """
        # consume any empty space
        while self.curr is not None and self.curr.isspace():
            self.step()
        if self.curr is None:
            self.error(f"Empty top-level expression")
        res = self.parse_expr()
        # consume any empty space
        while self.curr is not None and self.curr.isspace():
            self.step()
        if self.curr is not None:
            self.error(f"Invalid top-level expression")
        return res

    def parse_expr(self) -> Expression:
        """
        Parses the next expression

        EXPR := ATOM | LIST_EXPR
        """
        # consume any empty space
        while self.curr.isspace():
            self.step()
        if self.curr == '(':
            return self.parse_list_expression()
        elif self.curr == ')':
            self.error(f"Unexpected ')'")
        else:
            return self.parse_atom()

    def parse_list_expression(self) -> ListExpression:
        """
        Parses the next list expression

        LIST_EXPR := '(' WS* (EXPR WS+)* EXPR? WS* ')'
        """
        if self.curr != '(':
            self.error(f"Expecting '(' to start a list expression; got {self.curr} instead")
        start_line = self.lineno
        start_char = self.charno
        # consume '('
        self.step()
        sub_expressions = []
        while True:
            # consume any empty space
            while self.curr is not None and self.curr.isspace():
                self.step()
            if self.curr is None:
                self.error(f"List expression starting at {self.filename}:{start_line},{start_char} does not terminate")
            # capture end of listexpr
            if self.curr == ')':
                break
            # add sub expression
            expr = self.parse_expr()
            sub_expressions.append(expr)
        # consume ')'
        self.step()
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
        if self.curr in ('\'', '\"'):
            return self.parse_literal()
        elif self.curr in ('(', ')'):
            self.error(f"Unexpected '{self.curr}'")
        else:
            return self.parse_name()

    def parse_literal(self) -> Literal:
        """ Parses the next literal """
        if self.curr not in ('\'', '\"'):
            self.error(f"Expecting ' or \" to start literal; got {self.curr} instead")
        start_quote = self.curr
        start_line = self.lineno
        start_char = self.charno
        token = [self.curr]
        while True:
            token.append(self.step())
            if self.curr is None:
                self.error(f"Literal starting at {self.filename}:{start_line},{start_char} does not terminate")
            if self.curr == start_quote and self.prev != '\\':
                break
        self.step()
        # try to eval string
        token = ''.join(token)
        try:
            value = literal_eval(token)
        except Exception:
            self.error(f"Could not parse literal {token!r} correctly")
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
        start_line = self.lineno
        start_char = self.charno
        token = []
        while self.curr is not None and not self.curr.isspace() and self.curr not in ('(', ')'):
            token.append(self.curr)
            self.step()
        token = ''.join(token)
        return Name(
            token,
            filename=self.filename,
            start_line=start_line,
            start_char=start_char,
            end_line=self.lineno,
            end_char=self.charno)
