import typing


class Metadata(object):
    """
    Placeholder base type for metadata information.
    """


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

    def __str__(self):
        return f"{self.file}:{self.line}:{self.column}"

    def __eq__(self, other):
        if not isinstance(other, Location):
            return super(Location, self).__eq__(other)

        # Test lines and columns
        eq = self.line == other.line and self.column == other.column

        # Test files if present
        if self.file or other.file:
            eq = eq and self.file == other.file

        return eq

    def __ne__(self, other):
        return not self.__eq__(other)

    @property
    def is_line(self):
        return self.column == 0

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
