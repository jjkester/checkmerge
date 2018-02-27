import itertools
import typing

from checkmerge import analysis, diff, ir
from checkmerge.util import collections


class MemoryDependenceConflict(analysis.AnalysisResult):
    """
    Result of dependence analysis.
    """
    key: str = 'memory_dependence'
    name: str = 'Memory dependence conflict'
    description: str = 'Changes in nodes that may have an effect on the same memory.'
    severity: float = 1.0


class DependenceAnalysis(analysis.Analysis):
    """
    Analysis that finds conflicting changes in two versions of the program that may affect the same memory.
    """
    key: str = 'dependence'
    name: str = 'Dependence analysis'
    description: str = 'Finds changes in two versions that modify the same memory.'

    def __call__(self, changes: diff.DiffResult) -> analysis.AnalysisResultGenerator:
        results = []

        # Get all nodes that are of interest
        all_nodes = itertools.chain(changes.base.subtree(), changes.other.subtree())
        memory_nodes = filter(lambda n: n.is_memory_operation, all_nodes)

        # Iterate over all changed memory operations in both trees
        for node in memory_nodes:
            # Get all nodes possibly affected by a change in this node
            affected_nodes = {node}.union(self.get_affected(node))
            changed_nodes = {n for n in affected_nodes if n.is_changed}

            # If there is one changed node there is no problem
            if len(changed_nodes) > 1:
                results.append(changed_nodes)

        # Optimize and yield results
        results_changes = [
            {changes.changes_by_node.get(node) for node in result} - {None}
            for result in analysis.optimize_change_sets(results)
            if len({n.root for n in result}) > 1
        ]

        for result in collections.remove_subsets(results_changes):
            yield MemoryDependenceConflict(result, analysis=self)

    @classmethod
    def recursive_memory_dependencies(cls, node: ir.Node, reverse: bool = False) -> typing.Set[ir.Node]:
        nodes = [node]
        result = set()

        while len(nodes) > 0:
            # Get next node
            node = nodes.pop(0)

            if node in result:
                continue

            # Add to result
            result.add(node)

            # Add single-direction dependencies
            dependencies = node.reverse_dependencies if reverse else node.dependencies
            nodes.extend(d.node for d in filter(cls.is_memory_dependency, dependencies))

            if node.is_memory_operation:
                nodes.extend(node.descendants)

        return result

    @classmethod
    def get_dependencies(cls, node: ir.Node) -> typing.Generator[ir.Node, None, None]:
        """
        Collects the nodes in the dependency graph of the given node.

        :param node: The node to analyze.
        :return: A generator yielding the nodes in the dependency graph of the given node.
        """
        yield from set().union(
            cls.recursive_memory_dependencies(node, False),
            cls.recursive_memory_dependencies(node, True),
        )

    @classmethod
    def get_mapped(cls, nodes: typing.Iterable[ir.Node]) -> typing.Generator[ir.Node, None, None]:
        """
        Collects the corresponding nodes in the other version of the tree for the given nodes.

        :param nodes: The nodes to analyze.
        :return: A generator yielding the mapped nodes for the given nodes.
        """
        for node in nodes:
            if node.mapping is not None:
                yield node.mapping

    @classmethod
    def get_affected(cls, node: ir.Node) -> typing.Generator[ir.Node, None, None]:
        """
        Collects the nodes in the other version of the program that are possibly affected by a change to the given node.

        :param node: The node to analyze.
        :return: A generator yielding the possibly affected nodes.
        """
        dependencies = cls.get_dependencies(node)
        mapped = cls.get_mapped(dependencies)
        mapped_dependencies = itertools.chain(mapped, *map(cls.get_dependencies, mapped))
        yield from mapped_dependencies

    @staticmethod
    def is_memory_dependency(d: ir.Dependency) -> bool:
        return d.type.is_memory_dependency
