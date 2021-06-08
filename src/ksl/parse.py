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
    return Parser(source, path, indentation).parse_expr()


def parse_block(
    source: typing.Union[str, typing.TextIO],
    path: Path = "",
    indentation: typing.Optional[str] = None,
) -> ast.Node:
    return Parser(source, path, indentation).parse_block()


def parse_module(
    source: typing.Union[str, typing.TextIO],
    path: Path = "",
    indentation: typing.Optional[str] = None,
) -> ast.Node:
    return Parser(source, path, indentation).parse_module()


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
            lines.append(self._parse_block())
        return ast.Module(lines)

    def _parse_block(self) -> ast.Node:
        exprs: typing.List[ast.Node] = []
        exprs.append(self._parse_expr())
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
            exprs.append(self._parse_expr())
        self._optional(tokens.Semicolon)
        if type(self.lexer.curr) in (tokens.Nodent, tokens.Dedent, tokens.End):
            if len(exprs) < 2:
                self._error("line must contain at least 2 sub-expressions")
            return ast.Line(exprs)
        if type(self.lexer.curr) == tokens.Colon:
            self.lexer.next()
        if type(self.lexer.curr) == tokens.Indent:
            self.lexer.next()
            exprs.append(self._parse_block())
            while type(self.lexer.curr) != tokens.Dedent:
                self._assert(tokens.Nodent)
                exprs.append(self._parse_block())
            self.lexer.next()
            return ast.Paragraph(exprs)
        self._fail()

    def parse_block(self) -> ast.Node:
        self._assert(tokens.Start)
        self._assert(tokens.Nodent)
        return self._parse_block()

    def _parse_expr(self) -> ast.Node:
        if type(self.lexer.curr) == tokens.LParen:
            return self._parse_list_expr()
        return self._parse_value()

    def parse_expr(self) -> ast.Node:
        self._assert(tokens.Start)
        self._assert(tokens.Nodent)
        return self._parse_expr()

    def _parse_list_expr(self) -> ast.Expression:
        self._assert(tokens.LParen)
        exprs: typing.List[ast.Node] = []
        while type(self.lexer.curr) != tokens.RParen:
            exprs.append(self._parse_expr())
            self._optional(tokens.Comma)
        self._assert(tokens.RParen)
        return ast.Expression(exprs)

    def _parse_value(self) -> ast.Value:
        if type(self.lexer.curr) in (tokens.String, tokens.Integer, tokens.Float):
            res = ast.Literal(self.lexer.curr.value)
            self.lexer.next()
            return res
        if type(self.lexer.curr) == tokens.Name:
            res2 = ast.Name(typing.cast(str, self.lexer.curr.value))
            self.lexer.next()
            return res2
        if type(self.lexer.curr) == tokens.LBracket:
            return self._parse_list()
        if type(self.lexer.curr) == tokens.LCurly:
            return self._parse_set_or_map()
        self._fail()

    def _parse_list(self) -> ast.List:
        self._assert(tokens.LBracket)
        elems: typing.List[ast.Node] = []
        while type(self.lexer.curr) != tokens.RBracket:
            elems.append(self._parse_expr())
            self._assert(tokens.Comma)
        self.lexer.next()
        return ast.List(elems)

    def _parse_set_or_map(self) -> typing.Union[ast.Set, ast.Map]:
        self._assert(tokens.LCurly)
        if type(self.lexer.curr) == tokens.RCurly:
            # empty map literal "{}"
            return ast.Map(())
        first = self._parse_expr()
        if type(self.lexer.curr) == tokens.Colon:
            # parse as map
            exprs: typing.List[typing.Tuple[ast.Node, ast.Node]] = []
            self.lexer.next()
            second = self._parse_expr()
            exprs.append((first, second))
            while type(self.lexer.curr) != tokens.RCurly:
                first = self._parse_expr()
                self._assert(tokens.Colon)
                second = self._parse_expr()
                self._assert(tokens.Comma)
            return ast.Map(exprs)
        elif type(self.lexer.curr) == tokens.Comma:
            # parse as set
            exprs2: typing.List[ast.Node] = [first]
            self.lexer.next()
            while type(self.lexer.curr) != tokens.RCurly:
                exprs2.append(self._parse_expr())
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


if __name__ == "__main__":
    import sys

    while True:
        print(parse_block(sys.stdin, "stdin"))
