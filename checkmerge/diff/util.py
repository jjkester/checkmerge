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


def exists(iterable: typing.Iterable):
    """
    Returns `True` when the iterable has content, otherwise `False`.

    This function should be considerably faster than `len()` when used with iterables and generators when the exact
    length of an iterable is not of interest.
    """
    if hasattr(iterable, '__len__'):
        return len(iterable) > 0
    elif hasattr(iterable, '__length_hint__'):
        return iterable.__length_hint__() > 0
    raise TypeError(f"Unable to determine the length of type {type(iterable)}.")
