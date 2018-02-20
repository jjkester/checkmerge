import heapq
import typing


# Type definitions
T = typing.TypeVar('T')


class PriorityList(object):
    """
    Queue-like data structure that prioritizes smaller items. At any point, `pop()` is guaranteed to return the smallest
    object, or when multiple objects are equally small, one of these objects.
    """

    def __init__(self, key: typing.Optional[typing.Callable[[T], int]] = None):
        """
        :param key: Optional callable that calculates the ordering key for an object.
        """
        self.key = key
        self.data: typing.List[typing.Tuple[int, T]] = []

    def push(self, obj: T) -> None:
        """
        Adds the given object to the collection.

        :param obj: The object to add.
        """
        item = (self.key(obj), obj) if self.key else obj
        heapq.heappush(self.data, item)

    def pop(self) -> T:
        """
        Removes and returns the smallest object in the collection. If during construction of the list a key function was
        given, this key is used to determine the order of the object.

        :return: The smallest item in the collection.
        """
        data = heapq.heappop(self.data)
        return data[1] if self.key else data

    def pop_many(self) -> typing.List[T]:
        """
        Removes and returns all the smallest objects in the collection. If during construction of the list a key
        function was given, this key is used to determine the order of the object.

        :return: A list of the smallest items in the collection.
        """
        # Ensures that an IndexError is raised on an empty list
        items = [heapq.heappop(self.data)]

        # As long as we have items that are at least as small (min heap), keep popping
        while len(self.data) and self.data[0] <= items[0]:
            items.append(heapq.heappop(self.data))

        return list(map(lambda x: x[1], items)) if self.key else items

    def peek(self) -> T:
        """
        Returns the smallest object in the collection without removing it.

        :return: The smallest item in the collection.
        """
        data = self.data[0]
        return data[1] if self.key else data

    def open(self, iterable: typing.Iterable[T]) -> None:
        """
        Adds all items from the given iterable to the collection.

        :param iterable: The items to add.
        """
        for obj in iterable:
            self.push(obj)

    def __bool__(self):
        return bool(self.data)

    def __len__(self):
        return len(self.data)


def remove_subsets(sets: typing.Iterable[typing.Set[T]]) -> typing.Iterable[typing.Set[T]]:
    """
    Removes sets that are identical to or a subset of another set in the provided iterable.

    :param sets: An iterable containing the sets to make unique.
    :return: The remaining sets.
    """
    sets = list(sets)
    result = set()

    for s in sets:
        y = [x for x in sets if s != x and s.issubset(x)]
        if not y:
            result.add(frozenset(s))

    yield from (set(s) for s in result)


def exists(iterable: typing.Iterable[T], pred: typing.Optional[typing.Callable[[T], bool]] = None):
    """
    Iterates over the given iterable until a value is found that evaluates to true. If `pred` is given, this function
    will be used for the evaluation, otherwise the boolean value of the objects in the iterable are checked.
    Partially consumes the iterable.

    :param iterable: The iterable to check.
    :param pred: The predicate to check the objects against.
    :return: Whether an object satisfying the predicate exists in the iterable.
    """
    return False if next(filter(pred, iterable), False) is False else True
