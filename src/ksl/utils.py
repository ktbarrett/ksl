from typing import TypeVar, Callable, Any, cast
from typing import Iterable, Iterator, Deque, Tuple
from functools import lru_cache
from collections import deque


Func = TypeVar('Func', bound=Callable[..., Any])


def cached(func: Func) -> Func:
    return cast(Func, lru_cache(maxsize=None)(func))


T = TypeVar('T')


def window(iterable: Iterable[T], size: int) -> Iterator[Tuple[T, ...]]:
    iterator = iter(iterable)
    window: Deque[T] = deque(maxlen=size)
    for _, c in zip(range(size - 1), iterator):
        window.append(c)
    for c in iterator:
        window.append(c)
        yield tuple(window)
