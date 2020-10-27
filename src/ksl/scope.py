from typing import Dict, Any


class Scope:

    def __init__(self, parent: 'Scope'):
        self._parent = parent
        self._items: Dict[str, Any] = {}

    def enter(self) -> 'Scope':
        return Scope(self)

    def __getitem__(self, item: str):
        if item in self._items:
            return self._items[item]
        elif self._parent is None:
            raise KeyError(repr(item))
        else:
            return self._parent[item]

    def __setitem__(self, item: str, value: Any) -> None:
        self._items[item] = value

    def __delitem__(self, item: str) -> None:
        del self._items[item]
