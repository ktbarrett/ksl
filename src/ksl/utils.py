from typing import TypeVar, Callable, Any, cast
from functools import lru_cache


Func = TypeVar('Func', bound=Callable[..., Any])


def cached(func: Func) -> Func:
    return cast(Func, lru_cache(maxsize=None)(func))
