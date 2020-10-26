from itertools import chain
from collections import deque


class LexError(Exception):
    """
    Thrown when an error occurs during lex
    """


class Token:
    """
    """

    def __init__(self, s):
        self._s = s

    def __repr__(self):
        return self._s


class IntegerLiteral(Token):
    """
    Integer literal

    -?[0-9]+
    """


class StringLiteral(Token):
    r"""
    String literal

    "[^"]"
    """


class FloatLiteral(Token):
    """
    Float literal

    -?[0-9]+.[0-9]*
    """


class ExpressionListStart(Token):
    """
    Start of an expression list

    (
    """

    def __init__(self):
        super().__init__("(")


class ExpressionListEnd(Token):
    """
    End of an expression list

    )
    """

    def __init__(self):
        super().__init__(")")


class Name(Token):
    """
    Name binding to a function or value

    [_a-zA-Z][_-a-zA-Z0-9]*
    """


def lexer(s):
    lex_iter = iter(window(chain((None,), s), 2))

    for prev_c, c in lex_iter:
        if c.isspace():
            pass
        elif c == "\"":
            token_str = []
            # consume until first " is found
            for prev_c, c in lex_iter:
                if c == "\"" and prev_c != "\\":
                    yield StringLiteral("".join(token_str))
                    token_str.clear()
                    break
                token_str.append(c)
            else:
                raise LexError("Reach end of input without terminating string")
        elif c == "(":
            yield ExpressionListStart()
        elif c == ")":
            yield ExpressionListEnd()
        elif c == "-" or c.isdecimal():
            # lex as integer or float
            token_str = [c]
            ended = False
            # consume all digits
            for prev_c, c in lex_iter:
                if not c.isdecimal():
                    break
                token_str.append(c)
            else:
                ended = True
            if c != ".":
                # should be end
                if c.isspace() or ended:
                    yield IntegerLiteral("".join(token_str))
                else:
                    raise LexError("Bad Name, must start with '_' or an ASCII letter")
            else:
                token_str.append(c)
                ended = False
                # consume all digits
                for prev_c, c in lex_iter:
                    if not c.isdecimal():
                        break
                    token_str.append(c)
                else:
                    ended = True
                # should be end
                if c.isspace() or ended:
                    yield FloatLiteral("".join(token_str))
                else:
                    raise LexError("Bad Name, must start with '_' or an ASCII letter")
        elif c == '_' or c.isalpha():
            # lex as name
            token_str = [c]
            ended = False
            # consume all valid
            for prev_c, c in lex_iter:
                if not c.isalnum():
                    break
                token_str.append(c)
            else:
                ended = True
            if c.isspace() or ended:
                yield Name("".join(token_str))
            else:
                raise LexError("Bad Name, enconutered invalid character")
        else:
            raise LexError("Error could not lex")


def window(iterable, n):
    iterator = iter(iterable)
    w = deque()
    for _, v in zip(range(n), iterator):
        w.append(v)
    if len(w) == n:
        yield tuple(w)
    for v in iterator:
        w.popleft()
        w.append(v)
        yield tuple(w)
