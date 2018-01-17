import typing

from checkmerge import diff, ir


AnalysisResultGenerator = typing.Generator["AnalysisResult", None, None]


class AnalysisResult(object):
    """
    Base class for results of an analysis.
    """
    key: str = ''
    name: str = ''
    description: str = ''
    severity: float = 0.0

    def __init__(self, *conflicting_changes: diff.Change, analysis: "Analysis"):
        self.analysis = analysis
        self.changes = conflicting_changes

    def __repr__(self):
        return f"<AnalysisResult: {self.analysis.key}>"

    def __str__(self):
        return f"{self.analysis.name} ({len(self.changes)})"


class Analysis(object):
    """
    Base class for analysis implementations.
    """
    key: str = ''
    name: str = ''
    description: str = ''

    def __call__(self, base: ir.IRNode, other: ir.IRNode, changes: diff.DiffResult) -> AnalysisResultGenerator:
        """
        Runs the analysis on the provided trees and diff result. Yields an analysis result for

        :param base: The base tree.
        :param other: The compared tree.
        :param changes: The diff result of the provided trees.
        :return: Generator of the results of this analysis.
        """
        raise NotImplementedError()
