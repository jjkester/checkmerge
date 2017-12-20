import abc
import collections
import heapq
import typing


# Type definitions
T = typing.TypeVar('T')


class PriorityList(object):
    def __init__(self, key: typing.Optional[typing.Callable[[T], int]] = None):
        self.key = key
        self.data: typing.List[typing.Tuple[int, T]] = []

    def push(self, obj: T) -> None:
        item = (self.key(obj), obj) if self.key else obj
        heapq.heappush(self.data, item)

    def pop(self) -> T:
        data = heapq.heappop(self.data)
        return data[1] if self.key else data

    def pop_many(self) -> typing.List[T]:
        # Ensures that an IndexError is raised on an empty list
        items = [heapq.heappop(self.data)]

        # As long as we have items that are at least as small (min heap), keep popping
        while len(self.data) and self.data[0] <= items[0]:
            items.append(heapq.heappop(self.data))

        return list(map(lambda x: x[1], items)) if self.key else items

    def peek(self) -> T:
        data = self.data[0]
        return data[1] if self.key else data

    def open(self, iterable: typing.Iterable[T]) -> None:
        for obj in iterable:
            self.push(obj)

    def __bool__(self):
        return bool(self.data)

    def __len__(self):
        return len(self.data)


class ScopeBase(collections.MutableMapping, metaclass=abc.ABCMeta):
    """
    Base class for the Scope collection.
    """
    __slots__ = ()


class EmptyScope(ScopeBase):
    """
    An empty, no-op scope. Used as a (singleton) placeholder for empty parents.
    """
    __slots__ = ()

    def __setitem__(self, key, value):
        raise KeyError(key)

    def __delitem__(self, key):
        raise KeyError(key)

    def __getitem__(self, key):
        raise KeyError(key)

    def __len__(self):
        return 0

    def __iter__(self):
        yield from ()


class Scope(ScopeBase):
    EMPTY = EmptyScope()

    __slots__ = ('_parent', '_data')

    def __init__(self, parent: ScopeBase = EMPTY):
        # Check parent for validity
        if not isinstance(parent, ScopeBase):
            raise TypeError("Only instances of Scope can be used as parent.")

        # Initialize slots
        self._data = {}
        self._parent = parent

    @property
    def parent(self):
        return self._parent

    def __getitem__(self, key):
        if key in self._data:
            return self._data[key]
        return self._parent[key]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __delitem__(self, key):
        del self._data[key]

    def __len__(self):
        return len(set().union(self._data, self._parent))

    def __iter__(self):
        yield from set().union(self._data, self._parent)
