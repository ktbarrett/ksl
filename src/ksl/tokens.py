from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class Token:
    value: Optional[Any] = None


@dataclass(frozen=True)
class Indent(Token):
    pass


@dataclass(frozen=True)
class Nodent(Token):
    pass


@dataclass(frozen=True)
class Dedent(Token):
    pass


@dataclass(frozen=True)
class Name(Token):
    pass


@dataclass(frozen=True)
class Integer(Token):
    pass


@dataclass(frozen=True)
class Float(Token):
    pass


@dataclass(frozen=True)
class String(Token):
    pass


@dataclass(frozen=True)
class LParen(Token):
    pass


@dataclass(frozen=True)
class RParen(Token):
    pass


@dataclass(frozen=True)
class LCurly(Token):
    pass


@dataclass(frozen=True)
class RCurly(Token):
    pass


@dataclass(frozen=True)
class LBracket(Token):
    pass


@dataclass(frozen=True)
class RBracket(Token):
    pass


@dataclass(frozen=True)
class Colon(Token):
    pass


@dataclass(frozen=True)
class Comma(Token):
    pass


@dataclass(frozen=True)
class Semicolon(Token):
    pass


@dataclass(frozen=True)
class Tick(Token):
    pass


@dataclass(frozen=True)
class Start(Token):
    pass


@dataclass(frozen=True)
class End(Token):
    pass
