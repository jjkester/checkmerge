import collections
import itertools
import typing

from checkmerge import analysis, report


class AnalysisResultMaxSeverityMetric(report.Metric):
    """
    Metric for the maximum analysis result severity within a type.
    """
    name = 'Max. severity'
    low = .5
    high = 1.5

    def __init__(self, items: typing.List[analysis.AnalysisResult]):
        """
        :param cls: The type of analysis result.
        :param items: The results of the given type.
        """
        value = max((item.severity for item in items))
        super(AnalysisResultMaxSeverityMetric, self).__init__(value)


class AnalysisResultAvgSeverityMetric(report.Metric):
    """
    Metric for the average analysis result severity within a type.
    """
    name = 'Avg. severity'
    low = .5
    high = 1.5

    def __init__(self, items: typing.List[analysis.AnalysisResult]):
        """
        :param cls: The type of analysis result.
        :param items: The results of the given type.
        """
        value = sum((item.severity for item in items)) / float(len(items))
        super(AnalysisResultAvgSeverityMetric, self).__init__(value)


class AnalysisResultMetric(report.Metric):
    """
    Parent metric for types of analysis results.
    """
    low = 1
    high = 5

    def __init__(self, cls: typing.Type[analysis.AnalysisResult], items: typing.List[analysis.AnalysisResult]):
        self.name = cls.name
        items = list(items)
        max_severity = AnalysisResultMaxSeverityMetric(items)
        avg_severity = AnalysisResultAvgSeverityMetric(items)
        super(AnalysisResultMetric, self).__init__(len(items), children=[max_severity, avg_severity])


class AnalysisReport(report.Report):
    """
    Report for analysis results.
    """
    has_metrics = True
    has_conflicts = True

    def __init__(self, results: typing.Iterable[analysis.AnalysisResult]):
        self.results_by_type = collections.defaultdict(list)

        for result in results:
            self.results_by_type[result.__class__].append(result)

    def get_metrics(self) -> typing.Iterable[report.Metric]:
        for cls, items in sorted(self.results_by_type.items(), key=lambda i: i[0].name):
            yield AnalysisResultMetric(cls, items)

    def get_conflicts(self) -> typing.Iterable[analysis.AnalysisResult]:
        return sorted(itertools.chain(*self.results_by_type.values()), key=lambda r: -r.severity)
