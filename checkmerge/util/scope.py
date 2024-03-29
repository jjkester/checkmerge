import abc
import collections


class ScopeBase(collections.MutableMapping, metaclass=abc.ABCMeta):
    """
    Base class for the Scope collection. This base class exists to support both the regular Scope and the EmptyScope
    special-case.
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
    """
    Scope collection that can look up items from a parent scope, but not from sibling scopes.
    """
    EMPTY = EmptyScope()

    __slots__ = ('_parent', '_data')

    def __init__(self, parent: ScopeBase = EMPTY):
        """
        :param parent: The parent of this scope. Defaults to the emtpy scope.
        """
        # Check parent for validity
        if not isinstance(parent, ScopeBase):
            raise TypeError("Only instances of Scope can be used as parent.")

        # Initialize slots
        self._data = {}
        self._parent = parent

    @property
    def parent(self):
        """The parent of this scope."""
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
