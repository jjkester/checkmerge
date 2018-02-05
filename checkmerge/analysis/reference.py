import typing

import itertools

from checkmerge import analysis, diff, ir


class ReferenceAnalysisResult(analysis.AnalysisResult):
    """
    Result of reference analysis.
    """


class RenamedReferenceConflict(ReferenceAnalysisResult):
    key: str = 'renamed_reference'
    name: str = "Renamed reference conflict"
    description: str = "Dead or incorrect references to a renamed identifier."
    severity: float = 2.0


class DeletedReferenceConflict(ReferenceAnalysisResult):
    key: str = 'deleted_reference'
    name: str = "Deleted reference conflict"
    description: str = "Dead or incorrect references to a deleted identifier."
    severity: float = 1.5


class ReferenceAnalysis(analysis.Analysis):
    """
    Analysis that finds renamed or deleted identifiers and checks whether all references to it changed as well.
    """
    key: str = 'reference'
    name: str = "Reference analysis"
    description: str = "Finds changes in versions that lead to broken references to identifiers."

    def __call__(self, base: ir.Node, other: ir.Node, changes: diff.DiffResult) -> analysis.AnalysisResultGenerator:
        # Iterate over all changed nodes
        for node in itertools.chain(base.subtree(), other.subtree()):
            dependencies = list(self.get_dependencies(node))

            # Stop analysis for this node if it is not a definition
            if len(dependencies) == 0:
                continue

            conflicts = {changes.changes_by_node.get(node)}

            if node.mapping is None:
                conflict_type = DeletedReferenceConflict
                for dependency in dependencies:
                    if dependency.mapping is not None:
                        conflicts.add(dependency)
                        conflicts.add(dependency.mapping)
            else:
                conflict_type = RenamedReferenceConflict
                mapped_dependencies = set(self.get_dependencies(node.mapping))

                conflicts.add(changes.changes_by_node.get(node.mapping))

                for dependency in dependencies:
                    if dependency.mapping is not None and dependency.mapping not in mapped_dependencies:
                        local_conflicts = {
                            changes.changes_by_node.get(dependency),
                            changes.changes_by_node.get(dependency.mapping),
                        } - {None}

                        if len(local_conflicts) == 0:
                            if dependency.root == base:
                                change = diff.Change(dependency, dependency.mapping, diff.EditOperation.RENAME)
                            else:
                                change = diff.Change(dependency.mapping, dependency, diff.EditOperation.RENAME)
                            local_conflicts = {change}

                        conflicts.update(local_conflicts)

            if len(conflicts) > 1:
                yield conflict_type(*conflicts, analysis=self)

    @classmethod
    def get_dependencies(cls, node: ir.Node) -> typing.Generator[ir.Node, None, None]:
        """
        Collects the nodes referencing the given node.

        :param node: The node to analyze.
        :return: A generator yielding the nodes referencing this node.
        """
        yield from map(lambda x: x.node,
                       filter(lambda y: y.type == ir.DependencyType.REFERENCE and y.reverse is True,
                              node.reverse_dependencies))
