import typing
from functools import total_ordering


class Metadata(object):
    """
    Placeholder base type for metadata information.
    """
    __slots__ = ()

    def __repr__(self):
        return f"<{self.__class__.__name__} {self}>"

    def __str__(self):
        msg = f"The string representation of the Metadata subclass {self.__class__.__name__} should be implemented."
        raise NotImplementedError(msg)


@total_ordering
class Location(object):
    """
    Location in source code.
    """
    __slots__ = ('file', 'line', 'column')

    def __init__(self, file: str, line: int, column: int):
        """
        :param file: The file name or path. May be the empty string if unknown or irrelevant.
        :param line: The line number in the file.
        :param column: The column number in the line.
        """
        # Set properties
        self.file: str = file
        self.line: int = line
        self.column: int = column

    def as_tuple(self) -> typing.Tuple[str, int, int]:
        return self.file, self.line, self.column

    @property
    def coordinates(self) -> typing.Tuple[int, int]:
        return self.line, self.column

    @property
    def is_line(self) -> bool:
        return self.column == 0

    def __str__(self):
        return f"{self.file}:{self.line}:{self.column}"

    def __repr__(self):
        return f"<{self.__class__.__name__} {self}>"

    def __eq__(self, other):
        if not isinstance(other, Location):
            return NotImplemented

        # Test lines and columns
        eq = self.line == other.line and self.column == other.column

        # Test files if present
        if self.file or other.file:
            eq = eq and self.file == other.file

        return eq

    def __lt__(self, other):
        if not isinstance(other, Location):
            return NotImplemented
        if self.file and other.file:
            return self.as_tuple() < other.as_tuple()
        return self.coordinates < other.coordinates

    def __le__(self, other):
        if not isinstance(other, Location):
            return NotImplemented
        if self.file and other.file:
            return self.as_tuple() <= other.as_tuple()
        return self.coordinates <= other.coordinates

    def __hash__(self):
        return hash(str(self))

    @classmethod
    def parse(cls: typing.Type["Location"], value: str) -> typing.Optional["Location"]:
        """
        Parses a semicolon `:` separated location string in the format `filename:line:column`.

        :param value: The location string.
        :return: A new instance.
        """
        if len(value) == 0:
            return None

        segments = value.split(':')

        if len(segments) != 3:
            raise ValueError(f"The location string {value} is invalid.")

        file, line, column = segments

        return cls(file, int(line), int(column))


class Range(object):
    """
    Range of locations in source code.
    """
    __slots__ = ('start', 'end')

    def __init__(self, start: Location, end: Location):
        """
        :param start: The start location of this range. The start location file and end location file must be equal.
        :param end: The end location of this range. The start location file and end location file must be equal.
        """
        assert start.file == end.file

        self.start = start
        self.end = end

    def as_tuple(self) -> typing.Tuple[typing.Tuple[str, int, int], typing.Tuple[str, int, int]]:
        return self.start.as_tuple(), self.end.as_tuple()

    @property
    def lines(self) -> typing.Iterable[int]:
        """The line numbers in this range."""
        return range(self.start.line, self.end.line + 1)

    def overlaps(self, other: "Range"):
        """
        Tests whether this range (partially) overlaps with the given range. Ranges overlap also when a range is
        contained in another range. This test is commutative.

        :param other: The other range to test.
        :return: Whether this range overlaps with the given range.
        """
        return other.start <= self.start < other.end or other.start < self.end <= other.end

    def contains(self, other: typing.Union[Location, "Range"]):
        """
        Tests whether a given range or location is contained by this range.
        :param other:
        :return:
        """
        if isinstance(other, Location):
            return self.start <= other < self.end
        return self.start <= other.start and other.end <= self.end

    def __str__(self):
        return f"{self.start.file}:{self.start.coordinates}:{self.end.coordinates}"

    def __repr__(self):
        return f"<Range {self}>"

    def __eq__(self, other):
        if not isinstance(other, Range):
            return NotImplemented
        return self.start == other.start and self.end == other.end

    def __ne__(self, other):
        return not self == other

    def __contains__(self, item):
        if isinstance(item, Range):
            return self.overlaps(item)
        elif isinstance(item, Location):
            return self.contains(item)
        return super(Range, self).__contains__(item)

    def __hash__(self):
        return hash(str(self))

    @classmethod
    def compress(cls, *ranges: "Range") -> typing.List["Range"]:
        """
        Compresses the given ranges. Two ranges will be merged if they overlap. The results will be sorted by lower
        bound.

        :param ranges: The ranges to compress.
        :return: A set containing the compressed ranges.
        """
        sorted_ranges = sorted(ranges, key=lambda r: r.start)
        result = [next(sorted_ranges)] if len(ranges) > 0 else []

        for higher in ranges:
            lower = result[-1]

            if higher.overlaps(lower) and lower.end < higher.end:
                result[-1] = cls(lower.start, higher.end)
            else:
                result.append(higher)

        return result
