import typing

import itertools

from checkmerge import diff, ir
from checkmerge.util.collections import remove_subsets


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
        return f"<{self.__class__.__name__}: {str(self)}>"

    def __str__(self):
        return f"{self.name} ({len(self.changes)} changes)"

    def __hash__(self):
        return hash((self.__class__, self.analysis, self.changes))

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.analysis == other.analysis and self.changes == other.changes

    def get_base_nodes(self) -> typing.Set[ir.Node]:
        """
        :return: The nodes from the base tree in the changes in this result.
        """
        return {change.base for change in self.changes if change.base is not None}

    def get_other_nodes(self) -> typing.Set[ir.Node]:
        """
        :return: The nodes from the other tree in the changes in this result.
        """
        return {change.other for change in self.changes if change.other is not None}

    def get_base_locations(self) -> typing.Set[ir.Range]:
        """
        :return: The set of (compressed) locations in the base tree affected by this conflict.
        """
        return set(ir.Range.compress(*map(lambda n: n.source_range, self.get_base_nodes())))

    def get_other_locations(self) -> typing.Set[ir.Range]:
        """
        :return: The set of (compressed) locations in the other tree affected by this conflict.
        """
        return set(ir.Range.compress(*map(lambda n: n.source_range, self.get_other_nodes())))


class Analysis(object):
    """
    Base class for analysis implementations.
    """
    key: str = ''
    name: str = ''
    description: str = ''

    def __call__(self, base: ir.Node, other: ir.Node, changes: diff.DiffResult) -> AnalysisResultGenerator:
        """
        Runs the analysis on the provided trees and diff result. Yields an analysis result for

        :param base: The base tree.
        :param other: The compared tree.
        :param changes: The diff result of the provided trees.
        :return: Generator of the results of this analysis.
        """
        raise NotImplementedError()


def optimize_change_sets(change_sets: typing.Iterable[typing.Set[ir.Node]]) -> typing.Iterable[typing.Set[ir.Node]]:
    """
    Optimizes sets of changes in a number of ways to remove sets covering the same changes.

    Optimizations include:
    - Nodes that are descendants of another node present in the set are replaced by that node.
    - Sets of nodes that are subsets of another set of nodes are removed.

    :param change_sets: A set containing sets of changed nodes.
    :return: A generator yielding sets of changed nodes.
    """
    replaces = {}

    # Remove duplicates before carrying out expensive algorithm
    change_sets = list(remove_subsets(change_sets))

    # Iterate over all combinations of two change sets to build a replacement mapping
    for cs1, cs2 in itertools.product(change_sets, change_sets):
        # Iterate over all combinations of the changes in the sets
        for c1, c2 in itertools.product(cs1, cs2):
            # Set replacement if a node is a descendant of
            if c1 in c2.descendants:
                replaces[c1] = replaces.get(c2, c2)
            elif c2 in c1.descendants:
                replaces[c2] = replaces.get(c1, c1)

    # Carry out replacements and yield the results
    yield from remove_subsets({replaces.get(c, c) for c in cs} for cs in change_sets)
