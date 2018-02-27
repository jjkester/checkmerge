import linecache
import os
import typing

import click

from checkmerge import analysis, diff, ir, report


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
        sorted_children = sorted(node.children, key=lambda n: n.location)
        start = min(node.source_range.start,
                    sorted_children[0].source_range.start) if sorted_children else node.source_range.start
        for child in sorted_children:
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

    if len(ranges) == 0:
        return ''

    # Fill in ranges
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


def format_conflict(conflict: analysis.AnalysisResult):
    """
    Formats a conflict from analysis.

    :param conflict: The analysis result to format.
    :return: The formatted analysis result.
    """
    buffer = []

    buffer.append(click.style(f"CONFLICT: {conflict.name}", bold=True))
    buffer.append(click.style(f"Severity: {conflict.severity:.2f}"))

    indent_continuation = click.style('│ ', fg='gray')
    indent_item = click.style('├─', fg='gray')

    for change in conflict.changes:
        change_lines = format_change(change).split(os.linesep)

        if len(change_lines) > 0:
            buffer.append(f"{indent_item}{change_lines[0]}")

            for line in change_lines[1:]:
                buffer.append(f"{indent_continuation}{line}")

    buffer.append(click.style('└───', fg='gray'))

    return os.linesep.join(buffer)


class CheckMergeFormatter(click.HelpFormatter):
    """
    CheckMerge specific CLI formatter.
    """

    def write_text(self, text, wrap=True):
        if wrap:
            super().write_text(text)
        else:
            for line in text.split(os.linesep):
                self.write('%*s%s%s' % (self.current_indent, '', line, os.linesep))

    def write_heading(self, heading):
        self.write(click.style('%*s%s:\n' % (self.current_indent, '', heading), bold=True))

    def write_change(self, change: diff.Change):
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
            self.write_text(format_filename(change.base.location.file, '-'), False)
        if other_lines:
            self.write_text(format_filename(change.other.location.file, '+'), False)
        if base_lines or other_lines:
            self.write_text(format_line_diff(base_lines, other_lines), False)

        if base_code:
            self.write_text(base_code, False)
        if other_code:
            self.write_text(other_code, False)

    def write_conflict(self, conflict: analysis.AnalysisResult):
        with self.section(f"{conflict.name} (severity: {conflict.severity})"):
            for change in conflict.changes:
                self.write_change(change)

    def get_metric_dl(self, metric: report.Metric, indent=0):
        rows = [(f"{' ' * indent}{metric.name}", metric.value_as_str())]

        for child in metric.children:
            rows.extend(self.get_metric_dl(child, indent + self.indent_increment))

        return rows

    def write_metric(self, metric: report.Metric):
        self.write_dl(self.get_metric_dl(metric))

    def write_report(self, data: report.Report):
        if data.has_metrics:
            for metric in data.get_metrics():
                self.write_metric(metric)

        if data.has_conflicts:
            for conflict in data.get_conflicts():
                self.write_conflict(conflict)

        if data.has_changes:
            for change in data.get_changes():
                self.write_change(change)
