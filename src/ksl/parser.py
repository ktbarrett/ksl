r"""
Recursive descent parse for a LISP

integer     = -?[0-9]+                      doesn't handle binary, octal, or hexadecimal literals yet
float       = -?[0-9]*.[0-9]*               support e notation later
string      = ".*"                          simplistic, but will be expanded later
name        =        basically anything that isn't something else separated by a string
expression  = \((integer|float|string|name)*\)
"""
import re


class BadParse(Exception):
    """Thrown when a sub expression could not be parsed"""


def parse(expression: str):
    expression = expression.strip()

    if expression[0] == '(':
        # try parsing as list
        if expression[-1] != ')':
            # not a valid set of matching parens
            raise BadParse(expression)
        # remove parens
        expression = expression[1:-1]
        # split into sub expressions
        # must first group valid string literals before splitting on spaces
        splits = re.split(_string_split, expression)
        # strip and split the even (non-matching) sub expressions
        sub_expressions = []
        for i, split in enumerate(splits):
            if i % 2 == 0:
                sub_expressions.extend(split.strip().split())
            else:
                sub_expressions.append(split)
        # clean up sub expression list by removing empty ones
        sub_expressions = [s for s in sub_expressions if s]
        # return as a list
        return tuple(parse(s) for s in sub_expressions)

    if expression[0] in _int_start_char:
        # try parsing as a integer

    if expression[0] in _float_start_char:
        # try parsing as a float

    # try parsing as a name

    # don't know, fail
    raise BadParse(expression)


_string_split = re.compile(r"(\".*\")")
