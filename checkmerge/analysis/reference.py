import typing

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

    def __call__(self, changes: diff.DiffResult) -> analysis.AnalysisResultGenerator:
        # Exit if the diff is not a three-way diff
        if not isinstance(changes, diff.MergeDiffResult):
            return

        # Iterate over all declarations
        for declaration in filter(lambda n: n.is_definition, changes.ancestor.subtree()):
            # Get relevant changes in the declaration
            base_change: diff.Change = changes.base_changes_by_node.get(declaration)
            other_change: diff.Change = changes.other_changes_by_node.get(declaration)

            # Do analysis if there is a change
            if base_change is not None or other_change is not None:
                # Get all uses of the declaration
                uses = set(self.get_uses(declaration))

                # Get declarations in other versions
                base_declaration = changes.base_mapping.get(declaration)
                other_declaration = changes.other_mapping.get(declaration)
                declarations = {base_declaration, other_declaration} - {None}

                if base_change is not None and other_declaration is not None:
                    other_uses = set(self.get_uses(other_declaration))
                    conflicting_nodes = other_uses.difference(map(changes.other_mapping.get, uses)).union(declarations)
                    yield from self.get_conflict(base_change.op, conflicting_nodes, changes)
                if other_change is not None and base_declaration is not None:
                    base_uses = set(self.get_uses(base_declaration))
                    conflicting_nodes = base_uses.difference(map(changes.base_mapping.get, uses)).union(declarations)
                    yield from self.get_conflict(other_change.op, conflicting_nodes, changes)

    @classmethod
    def get_uses(cls, node: ir.Node) -> typing.Generator[ir.Node, None, None]:
        """
        Yields the nodes using the given node.

        :param node: The node to get the uses for.
        :return: A generator yielding the nodes referencing the given node.
        """
        yield from (d.node for d in node.reverse_dependencies if d.type == ir.DependencyType.REFERENCE)

    def get_conflict(self, op: diff.EditOperation, nodes: typing.Iterable[ir.Node], result: diff.DiffResult):
        changes = set()
        base_nodes = set()
        other_nodes = set()

        for node in nodes:
            change = result.changes_by_node.get(node)

            if change:
                changes.add(change)
            elif node.root == result.base:
                base_nodes.add(node)
            elif node.root == result.other:
                other_nodes.add(node)

        if changes:
            if op == diff.EditOperation.RENAME:
                yield RenamedReferenceConflict(
                    changes=changes,
                    base_nodes=base_nodes,
                    other_nodes=other_nodes,
                    analysis=self,
                )
            elif op == diff.EditOperation.DELETE:
                yield DeletedReferenceConflict(
                    changes=changes,
                    base_nodes=base_nodes,
                    other_nodes=other_nodes,
                    analysis=self,
                )
