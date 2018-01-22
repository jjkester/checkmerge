import typing


# Type variables
KT = typing.TypeVar('KT')
VT = typing.TypeVar('VT')


class Registry(typing.Generic[KT, VT]):
    """
    A generic registry.
    """

    def __init__(self):
        self.registry: typing.Dict[KT, VT] = {}

    def register(self, cls: VT):
        """
        Registers the given class.

        :param cls: The class to register.
        """
        # Get key for class
        key = self.key(cls)

        if key is None or isinstance(key, bool) or key == '':
            raise ValueError(f"The key {repr(key)} is not a valid key.")

        if key not in self.registry:
            # Register if not registered
            self.registry[key] = cls
        elif key in self.registry and self.registry[key] != cls:
            # Raise if the registered class for this key is not this class
            raise ValueError(f"Cannot register class {cls.__name__}, a class with name {key} was already registered.")

    def key(self, cls: VT) -> KT:
        """
        Returns the unique lookup key for the given unregistered value.

        :param cls: The unregistered value.
        :return: The key.
        """
        raise NotImplementedError()

    def find(self, key: KT) -> typing.Optional[VT]:
        """
        Looks for the value corresponding to the given key and returns it. If no such value is registered or if the
        value is filtered out (see `_filter` below), `None` is returned.

        :param key: The lookup key.
        :return: The corresponding value or `None`.
        """
        item = self.registry.get(key, None)
        return item if self._filter(item) else None

    def all(self) -> typing.List[VT]:
        """
        Returns a list of all registered values with the filter applied (see `_filter` below).

        :return: A list of all usable registered values.
        """
        return list(filter(self._filter, self.registry.values()))

    def _filter(self, item: VT) -> bool:
        """
        A filter which returns either `True` or `False` to decide whether an item should be marked as 'usable'. This
        decides whether the item is returned in the lookup methods of the registry.

        :param item: The value to filter.
        :return: Whether the value should be included.
        """
        return True
