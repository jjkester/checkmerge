import typing
from functools import total_ordering


class Metadata(object):
    """
    Placeholder base type for metadata information.
    """


@total_ordering
class Location(object):
    """
    Location in source code.
    """
    __slots__ = ('file', 'line', 'column')

    def __init__(self, file: str, line: int, column: int):
        """
        :param file: The file name or path. May be the empty string if unknown.
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
        return f"<{self.__class__.__name__}: {str(self)}>"

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
