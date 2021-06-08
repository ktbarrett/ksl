import typing
from dataclasses import dataclass


class Node:
    """ """


class Expression(typing.List["Node"], Node):
    """ """


class Module(Expression):
    """ """


class Block(Expression):
    """ """


class Line(Block):
    """ """


class Paragraph(Block):
    """ """


class Value(Node):
    """ """


@dataclass(frozen=True)
class Literal(Value):
    """ """

    value: typing.Any


@dataclass(frozen=True)
class Name(Value):
    """ """

    name: str


class Composite(Value):
    """ """


class List(typing.List["Node"], Composite):
    """ """


class Set(typing.List["Node"], Composite):
    """ """


class Map(typing.List[typing.Tuple["Node", "Node"]], Composite):
    """ """
