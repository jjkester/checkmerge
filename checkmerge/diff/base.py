import enum
import typing

from checkmerge.ir import tree


# Diff algorithm types
DiffMapping = typing.Dict[tree.IRNode, tree.IRNode]
DiffChanges = typing.Dict[tree.IRNode, "EditOperation"]


class DiffAlgorithm(object):
    """
    Base class for diff algorithms.
    """
    def __call__(self, base: tree.IRNode, other: tree.IRNode) -> "DiffResult":
        """
        Runs the diff algorithm to calculate a mapping between nodes of the base tree and the other tree.

        :param base: The base tree.
        :param other: The tree to compare.
        :return: A mapping from nodes of the base tree to nodes of the other tree.
        """
        raise NotImplementedError()


class EditOperation(enum.Enum):
    """
    Kinds of operations for transforming a tree.
    """
    INSERT = '+'
    DELETE = '-'
    RENAME = '~'


class DiffResult(object):
    """
    Result of a tree diff operation.
    """
    def __init__(self, base: tree.IRNode, other: tree.IRNode, mapping: DiffMapping,
                 changes: typing.Optional[DiffChanges] = None):
        self._base: tree.IRNode = base
        self._other: tree.IRNode = other
        self._mapping: DiffMapping = mapping
        self._changes: typing.Optional[DiffChanges] = changes

    @property
    def base(self) -> tree.IRNode:
        return self._base

    @property
    def other(self) -> tree.IRNode:
        return self._other

    @property
    def mapping(self) -> DiffMapping:
        return self._mapping

    @property
    def changes(self) -> DiffChanges:
        if self._changes is None:
            self._changes = {n: o for n, o in calculate_changes(self.base, self.other, self.mapping)}
        return self._changes


def calculate_changes(base: tree.IRNode, other: tree.IRNode, mapping: DiffMapping):
    """
    Calculates and yields the changes required to transform the base tree into the other tree.

    :param base: The base tree to calculate the changes for.
    :param other: The other tree to calculate the changes for.
    :param mapping: The calculated mapping between nodes of both trees.
    :return: Generator yielding the changes between the base tree and other tree.
    """
    for node in base.subtree():
        if node not in mapping.keys():
            yield (node, EditOperation.DELETE)
        elif node.name != mapping[node].name:
            yield (node, EditOperation.RENAME)
    for node in other.subtree():
        if node not in mapping.values():
            yield (node, EditOperation.INSERT)
