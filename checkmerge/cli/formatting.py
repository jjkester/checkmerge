import linecache
import typing

import click
import os

from checkmerge import diff, ir


def format_filename(filename: str, symbol: str = ' '):
    """
    Formats file names for a diff.

    :param filename: The name of the file.
    :param symbol: The single char symbol to prepend the file name with.
    :return: The formatted file name.
    """
    return click.style(f"{symbol*3} {filename}", fg='white', bold=True)


def format_line_diff(base: str, other: str) -> str:
    """
    Formats the line identifier of a change.

    :param base: The base line number(s).
    :param other: The other line number(s).
    :return: The formatted line numbers.
    """
    buffer = []

    if base:
        buffer.append(f"-{base}")
    if other:
        buffer.append(f"+{other}")

    return click.style(f"@@ {' '.join(buffer)} @@", fg='cyan')


def node_ranges(node: ir.Node) -> typing.Iterable[typing.Tuple[typing.Tuple[int, int], typing.Tuple[int, int], bool]]:
    """
    Returns the ranges of a node that are relevant for a change in that specific node. Children are excluded, unless
    they have the same range as the given node.

    Line numbers are normalized to be 0-indexed starting from the first line the given node occurs on. Column numbers
    are normalized to be 0-indexed as well.

    :param node: The node to get the ranges for.
    :return: Tuples indicating the start and end coordinates of ranges with a boolean indicating whether the range is
    relevant for the node.
    """
    def coordinates(location: ir.Location):
        return location.line - node.location.line, location.column - 1

    if len(node.children) == 0:
        yield coordinates(node.source_range.start), coordinates(node.source_range.end), True
    elif len(node.children) == 1 and node.source_range == node.children[0].source_range:
        yield from node_ranges(node.children[0])
    else:
        start = node.source_range.start
        for child in sorted(node.children, key=lambda n: n.location):
            if child.source_range.start > start:
                yield coordinates(start), coordinates(child.source_range.start), True
            start = child.source_range.end
        if start < node.source_range.end:
            yield coordinates(start), coordinates(node.source_range.end), True


def format_node_in_code(node: ir.Node, symbol: str = '', color: typing.Optional[str] = None) -> str:
    """
    Formats a node within its surrounding code.

    :param node: The node to format.
    :param symbol: The symbol to prepend to every line (defaults to an empty string).
    :param color: The color to use (defaults to the default color).
    :return: The formatted node.
    """
    assert node.location.file
    ranges = sorted(node_ranges(node))

    # Fill in ranges
    if len(ranges) > 0:
        prev = ranges[0]
        for cur in ranges[1:].copy():
            if cur[0] != prev[1]:
                ranges.insert(ranges.index(cur), (prev[1], cur[0], False))
        if ranges[0][0][1] != 0:
            ranges.insert(0, ((ranges[0][0][0], 0), ranges[0][0], False))

    # Get all involved lines
    line_numbers = list(range(min(s[0] for s, e, t in ranges), max(e[0] for s, e, t in ranges) + 1))
    lines = [linecache.getline(node.location.file, l + node.location.line) for l in line_numbers]
    lines[-1] = lines[-1].rstrip()

    # Output buffer
    buffer = []

    for start, end, mark in ranges:
        if start[0] == end[0] and start[1] < end[1] and start[0] in line_numbers:
            # Add segment within a single line
            buffer.append(click.style(lines[start[0]][start[1]:end[1]], fg=color, reverse=mark))
        elif start[0] < end[0]:
            # Add segment on first line
            buffer.append(click.style(lines[start[0]][start[1]:], fg=color, reverse=mark))

            # Add segments on intermediate lines, if any
            for line in range(start[0] + 1, end[0]):
                buffer.append(click.style(lines[line], fg=color, reverse=mark))

            # Add segment on last line
            if end[0] in lines:
                buffer.append(click.style(lines[end[0]][:end[1]], fg=color, reverse=mark))

    if ranges[-1][1][0] < ranges[-1][1][1]:
        buffer.append(click.style(lines[ranges[-1][1][0]][ranges[-1][1][1]:], fg=color, reverse=False))

    buffer = ''.join(buffer).split(os.linesep)
    return click.style(symbol, fg=color) + f"{os.linesep}{symbol}".join(buffer).strip()


def format_change(change: diff.Change) -> str:
    """
    Formats a change.

    :param change: The change to format.
    :return: The formatted change.
    """
    buffer = []

    base_code = other_code = ''
    base_lines = other_lines = ''

    if change.base:
        base_code = format_node_in_code(change.base, '-', 'red')
        lines = len(base_code.split('\n'))
        base_lines = f"{change.base.location.line},{change.base.location.line + lines}"
    if change.other:
        other_code = format_node_in_code(change.other, '+', 'green')
        lines = len(other_code.split('\n'))
        other_lines = f"{change.other.location.line},{change.other.location.line + lines}"

    if base_lines:
        buffer.append(format_filename(change.base.location.file, '-'))
    if other_lines:
        buffer.append(format_filename(change.other.location.file, '+'))
    if base_lines or other_lines:
        buffer.append(format_line_diff(base_lines, other_lines))

    if base_code:
        buffer.append(base_code)
    if other_code:
        buffer.append(other_code)

    return os.linesep.join(buffer)
