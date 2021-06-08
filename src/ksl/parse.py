import typing

import ksl.ast as ast
import ksl.tokens as tokens
from ksl.lex import Lexer
from ksl.types import Path


class ParseError(Exception):
    """Code does not contain a valid parse"""


def parse_expr(
    source: typing.Union[str, typing.TextIO],
    path: Path = "",
    indentation: typing.Optional[str] = None,
) -> ast.Node:
    parser = Parser(source, path, indentation)
    parser.lexer.next()
    parser.lexer.next()
    return parser.parse_expr()


def parse_block(
    source: typing.Union[str, typing.TextIO],
    path: Path = "",
    indentation: typing.Optional[str] = None,
) -> ast.Node:
    parser = Parser(source, path, indentation)
    parser.lexer.next()
    parser.lexer.next()
    return parser.parse_block()


def parse_module(
    source: typing.Union[str, typing.TextIO],
    path: Path = "",
    indentation: typing.Optional[str] = None,
) -> ast.Node:
    parser = Parser(source, path, indentation)
    return parser.parse_module()


class Parser:
    lexer: Lexer

    def __init__(
        self,
        source: typing.Union[str, typing.TextIO],
        path: Path,
        indentation: typing.Optional[str] = None,
    ):
        self.lexer = Lexer(source=source, path=path, indentation=indentation)

    def parse_module(self) -> ast.Module:
        self._assert(tokens.Start)
        lines: typing.List[ast.Node] = []
        while self.lexer.curr != tokens.End:
            self._assert(tokens.Nodent)
            lines.append(self.parse_block())
        return ast.Module(lines)

    def parse_block(self) -> ast.Node:
        exprs: typing.List[ast.Node] = []
        exprs.append(self.parse_expr())
        if type(self.lexer.curr) in (
            tokens.Indent,
            tokens.Nodent,
            tokens.Dedent,
            tokens.End,
        ):
            return exprs[0]
        while type(self.lexer.curr) not in (
            tokens.Semicolon,
            tokens.Indent,
            tokens.Nodent,
            tokens.Dedent,
            tokens.End,
        ):
            exprs.append(self.parse_expr())
        self._optional(tokens.Semicolon)
        if type(self.lexer.curr) in (tokens.Nodent, tokens.Dedent, tokens.End):
            if len(exprs) < 2:
                self._error("line must contain at least 2 sub-expressions")
            return ast.Line(exprs)
        if type(self.lexer.curr) == tokens.Colon:
            self.lexer.next()
        if type(self.lexer.curr) == tokens.Indent:
            self.lexer.next()
            exprs.append(self.parse_block())
            while type(self.lexer.curr) != tokens.Dedent:
                self._assert(tokens.Nodent)
                exprs.append(self.parse_block())
            self.lexer.next()
            return ast.Paragraph(exprs)
        self._fail()

    def parse_expr(self) -> ast.Node:
        if type(self.lexer.curr) == tokens.LParen:
            return self.parse_list_expr()
        return self.parse_value()

    def parse_list_expr(self) -> ast.Expression:
        self._assert(tokens.LParen)
        exprs: typing.List[ast.Node] = []
        while type(self.lexer.curr) != tokens.RParen:
            exprs.append(self.parse_expr())
            self._optional(tokens.Comma)
        self._assert(tokens.RParen)
        return ast.Expression(exprs)

    def parse_value(self) -> ast.Value:
        if type(self.lexer.curr) in (tokens.String, tokens.Integer, tokens.Float):
            res = ast.Literal(self.lexer.curr.value)
            self.lexer.next()
            return res
        if type(self.lexer.curr) == tokens.Name:
            res2 = ast.Name(typing.cast(str, self.lexer.curr.value))
            self.lexer.next()
            return res2
        if type(self.lexer.curr) == tokens.LBracket:
            return self.parse_list()
        if type(self.lexer.curr) == tokens.LCurly:
            return self.parse_set_or_map()
        self._fail()

    def parse_list(self) -> ast.List:
        self._assert(tokens.LBracket)
        elems: typing.List[ast.Node] = []
        while type(self.lexer.curr) != tokens.RBracket:
            elems.append(self.parse_expr())
            self._assert(tokens.Comma)
        self.lexer.next()
        return ast.List(elems)

    def parse_set_or_map(self) -> typing.Union[ast.Set, ast.Map]:
        self._assert(tokens.LCurly)
        if type(self.lexer.curr) == tokens.RCurly:
            # empty map literal "{}"
            return ast.Map(())
        first = self.parse_expr()
        if type(self.lexer.curr) == tokens.Colon:
            # parse as map
            exprs: typing.List[typing.Tuple[ast.Node, ast.Node]] = []
            self.lexer.next()
            second = self.parse_expr()
            exprs.append((first, second))
            while type(self.lexer.curr) != tokens.RCurly:
                first = self.parse_expr()
                self._assert(tokens.Colon)
                second = self.parse_expr()
                self._assert(tokens.Comma)
            return ast.Map(exprs)
        elif type(self.lexer.curr) == tokens.Comma:
            # parse as set
            exprs2: typing.List[ast.Node] = [first]
            self.lexer.next()
            while type(self.lexer.curr) != tokens.RCurly:
                exprs2.append(self.parse_expr())
                self._assert(tokens.Comma)
        self._fail()

    def _assert(self, expected: typing.Type[tokens.Token]) -> None:
        """
        Check if current token is expected one and consumes it.

        Passing :value:`None` or giving no argument causes the assert to always fail
        and error.
        """
        if type(self.lexer.curr) != expected:
            self._error(
                f"expected token of type: {expected.__name__}, found: {self.lexer.curr}"
            )
        self.lexer.next()

    def _fail(self) -> typing.NoReturn:
        self._error(f"unexpected token: {self.lexer.curr}")

    def _optional(self, expected: typing.Type[tokens.Token]) -> None:
        """
        Check if the current token is the expected one and consumes it only if it is
        """
        if type(self.lexer.curr) == expected:
            self.lexer.next()

    def _error(self, msg: str) -> typing.NoReturn:
        """Formats and raises a ParseError"""
        raise ParseError(msg)
