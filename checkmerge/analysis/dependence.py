import typing

import itertools

from checkmerge import analysis, ir, diff


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

    """
    key: str = 'dependence'
    name: str = 'Dependence analysis'
    description: str = ''

    def __call__(self, base: ir.IRNode, other: ir.IRNode, changes: diff.DiffResult) -> analysis.AnalysisResultGenerator:
        results = []

        # Iterate over memory operations in both trees
        for node in filter(lambda n: n.is_memory_operation, itertools.chain(base.subtree(), other.subtree())):
            changed_nodes = set(self.changes(node))
            dependencies = set(self.dependencies(node))

            if node.mapping is not None:
                changed_nodes.update(self.changes(node.mapping))
                dependencies.update(self.dependencies(node.mapping))

            # Iterate over dependency graph of the memory operation
            for dependency in dependencies:
                changed_nodes.update(self.changes(dependency))

            if len(changed_nodes) > 1:
                conflicts = set(map(changes.changes_by_node.get, changed_nodes))

                # Test whether we have a "real" conflict between changes from both versions
                has_base, has_other = False, False
                for change in conflicts:
                    if change.base is not None:
                        has_base = True
                    if change.other is not None:
                        has_other = True

                if len(conflicts) > 1 and has_base and has_other:
                    results.append(conflicts)

        # Compress results by removing subsets
        for result in results:
            is_subset = False

            for compare in results:
                # If another result contains this result, do not yield this result
                if result != compare and compare.issuperset(result):
                    is_subset = True
                    break

            if not is_subset:
                yield MemoryDependenceConflict(*result, analysis=self)

    def changes(self, node: ir.IRNode) -> typing.Generator[ir.IRNode, None, None]:
        for child in node.subtree():
            if child.is_changed:
                yield child
            if child.mapping is not None:
                for mapped_child in child.mapping.subtree():
                    if mapped_child.is_changed:
                        yield mapped_child

    def dependencies(self, node: ir.IRNode) -> typing.Generator[ir.IRNode, None, None]:
        yield from node.recursive_dependencies(recurse_memory_ops=True)
        yield from node.recursive_reverse_dependencies(recurse_memory_ops=True)
