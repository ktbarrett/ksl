from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Optional


class TokenType(Enum):
    Indent = auto()
    Nodent = auto()
    Dedent = auto()
    Identifier = auto()
    Integer = auto()
    Float = auto()
    String = auto()
    LParen = auto()
    RParen = auto()
    LCurly = auto()
    RCurly = auto()
    LBracket = auto()
    RBracket = auto()
    Colon = auto()
    Comma = auto()
    Semicolon = auto()
    Tick = auto()
    Start = auto()
    End = auto()


@dataclass(frozen=True)
class Token:
    type: TokenType
    value: Optional[Any] = None
