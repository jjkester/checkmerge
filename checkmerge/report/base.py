import typing

from checkmerge import diff, analysis


T = typing.TypeVar('T')


class Metric(typing.Generic[T], object):
    """
    Base class of a metric.
    """
    name: str = ''
    low: T = None
    high: T = None

    def __init__(self, value: T, children: typing.Optional[typing.Iterable["Metric"]] = None):
        """
        :param value: The actual value.
        """
        self.value = value
        self.children = list(children) if children is not None else []

    def value_as_str(self) -> str:
        """
        :return: The string format of the value.
        """
        return str(self.value)

    def is_low(self) -> bool:
        """
        :return: Whether the value is to be considered "low". May result in a green color in the output.
        """
        return self.value <= self.low

    def is_mid(self) -> bool:
        """
        :return: Whether the value is to be considered "medium". May result in a orange color in the output.
        """
        return not (self.is_low or self.is_high)

    def is_high(self) -> bool:
        """
        :return: Whether the value is to be considered "high". May result in a red color in the output.
        """
        return self.value >= self.high

    def as_tuple(self) -> typing.Tuple[str, T]:
        return self.name, self.value

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.value}>"

    def __str__(self):
        return f"{self.name}: {self.value}"


class Report(object):
    """
    Base class for reports.
    """

    def get_metrics(self) -> typing.Iterable[Metric]:
        """
        Calculates and returns metrics about the data the report is created for. Requires the `has_metrics` property to
        be `True`.

        :return: An iterable of metrics to report.
        """
        yield from ()

    def get_changes(self) -> typing.Iterable[diff.Change]:
        """
        Returns the changes that need to be reported on. Requires the `has_changes` property to be `True`.

        :return: An iterable of changes to report.
        """
        yield from ()

    def get_conflicts(self) -> typing.Iterable[analysis.AnalysisResult]:
        """
        Returns the conflicts that need to be reported on. Requires the `has_conflicts` property to be `True`.

        :return: An iterable of conflicts to report.
        """
        yield from ()

    @property
    def has_metrics(self) -> bool:
        """Whether this report supplies metrics."""
        return False

    @property
    def has_changes(self) -> bool:
        """Whether this report supplies changes."""
        return False

    @property
    def has_conflicts(self) -> bool:
        """Whether this report supplies conflicts."""
        return False
