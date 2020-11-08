from typing import Iterable, Optional, Union, List, Any, Type
from os import PathLike
from itertools import chain
from ast import literal_eval
from .utils import window
from .engine import Expression, ListExpression, Name, Literal


def parse(source: Optional[Iterable[str]] = None, filename: Optional[Union[str, PathLike]] = None) -> Expression:
    if source is not None:
        if filename is None:
            filename = "unknown"
    elif filename is not None:
        source = (char for line in open(filename) for char in line)
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
        for self._prev, self._curr in window(chain((None,), source), 2):
            yield self._curr
            if self._curr == '\n':
                self._lineno += 1
                self._charno = 1
            else:
                self._charno += 1
        self._prev = None
        self._curr = None

    def _step(self) -> None:
        """ Step to the next character in the input """
        try:
            next(self._iter)
        except StopIteration:
            pass

    def _error(self, msg: str) -> None:
        """ Create and raise a ParseError """
        raise ParseError(f"{self._filename}:{self._lineno},{self._charno} | " + msg)

    def _parse_whitespace(self) -> None:
        # consume any empty space
        while self._curr is not None and self._curr.isspace():
            self._step()

    def parse(self) -> Expression:
        """ Top level parser entry function for scripts """
        self._parse_whitespace()
        # if end of string the input was just whitespace
        if self._curr is None:
            self._error(f"Empty top-level expression")
        # parse an expression
        res = self._parse_expr()
        # consume any empty space
        self._parse_whitespace()
        # unexpectedly got something else
        if self._curr is not None:
            self._error(f"Invalid top-level expression")
        return res

    def _parse_expr(self) -> Expression:
        """
        Parses the next expression

        EXPR := ATOM | LIST_EXPR
        """
        # decide how to parse expression, is it a list, an atom, or malformed?
        if self._curr == '(':
            return self._parse_list_expression()
        return self._parse_atom()

    def _parse_list_expression(self) -> ListExpression:
        """
        Parses the next list expression

        LIST_EXPR := '(' WS* (EXPR WS+)* EXPR WS* ')'
        """
        start_line = self._lineno
        start_char = self._charno
        # consume '('
        self._step()
        sub_expressions = []
        # consume any empty space
        self._parse_whitespace()
        if self._curr == ')':
            msg = f"List expression starting at {self._filename}:{start_line},{start_char} is empty"
            self._error(msg)
        while True:
            expr = self._parse_expr()
            sub_expressions.append(expr)
            if self._curr is None:
                msg = f"List expression starting at {self._filename}:{start_line},{start_char} does not terminate"
                self._error(msg)
            elif self._curr == ')':
                # end of list expression
                break
            elif not self._curr.isspace():
                self._error("Missing whitespace?")
            # consume any empty space
            self._parse_whitespace()
        # consume ')'
        self._step()
        # yield a list expression
        return ListExpression(
            sub_expressions,
            filename=self._filename,
            start_line=start_line,
            start_char=start_char,
            end_line=self._lineno,
            end_char=self._charno)

    def _parse_atom(self) -> Expression:
        """
        Parses the next atom

        ATOM := LITERAL | NAME
        """
        # decide how to parse atom, is it a quoted literal, a name, or malformed?
        if self._curr in ('\'', '\"'):
            return self._parse_literal()
        return self._parse_other_atom()

    def _parse_literal(self) -> Literal:
        """ Parses the next literal """
        start_line = self._lineno
        start_char = self._charno
        # consume the quote
        start_quote = self._curr
        self._step()
        # consume everything between quotes
        token: List[str] = []
        while True:
            # if we reach the end of input, the string did not terminate
            if self._curr is None:
                self._error(f"Literal starting at {self._filename}:{start_line},{start_char} does not terminate")
            # strings end when matching an unescaped quote of the same type that started the literal
            elif self._curr == start_quote and self._prev != '\\':
                # consume the ending quote and leave
                self._step()
                break
            else:
                token.append(self._curr)
                self._step()
        # try to eval string
        token_str = '"""' + ''.join(token) + '"""'
        try:
            value = literal_eval(token_str)
        except Exception:  # pragma: no cover
            self._error(f"Could not parse literal {token_str!r} correctly")  # pragma: no cover
        # yield the literal
        return Literal(
            value,
            filename=self._filename,
            start_line=start_line,
            start_char=start_char,
            end_line=self._lineno,
            end_char=self._charno)

    def _parse_other_atom(self) -> Union[Name, Literal]:
        r"""
        Parses the next name or the next number literal

        NUMBER|NAME := \S+
        NUMBER is whatever parses as an `int` or `float` using `literal_eval`
        """
        delimeters = (')', '(', '\'', '\"')
        start_line = self._lineno
        start_char = self._charno
        # consume name
        token: List[str] = []
        while self._curr is not None and not self._curr.isspace() and self._curr not in delimeters:
            token.append(self._curr)
            self._step()
        # yield a name
        token_str = ''.join(token)
        T: Union[Type[Literal], Type[Name]]
        value: Any
        try:
            value = literal_eval(token_str)
        except Exception:
            value = token_str
            T = Name
        else:
            if isinstance(value, (int, float)):
                T = Literal
            else:
                value = token_str
                T = Name
        return T(
            value,
            filename=self._filename,
            start_line=start_line,
            start_char=start_char,
            end_line=self._lineno,
            end_char=self._charno)
