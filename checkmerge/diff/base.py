import collections
import enum
import typing

from checkmerge.ir import tree


# Diff algorithm types
DiffMapping = typing.Dict[tree.Node, tree.Node]
ChangesGenerator = typing.Generator["Change", None, None]
DiffChanges = typing.List["Change"]


class DiffAlgorithm(object):
    """
    Base class for diff algorithms.
    """
    def __call__(self, base: tree.Node, other: tree.Node) -> "DiffResult":
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

    def __str__(self):
        return str(self.value)


class Change(object):
    """
    A change found by the diff algorithm.
    """
    __slots__ = ('base', 'other', 'op')

    def __init__(self, base: tree.Node, other: tree.Node, op: EditOperation):
        """
        :param base: The changed node in the base tree.
        :param other: The changed node in the other tree.
        :param op: The edit operation.
        """
        self.base = base
        self.other = other
        self.op = op

    def as_tuple(self) -> typing.Tuple[tree.Node, tree.Node, EditOperation]:
        return self.base, self.other, self.op

    def __getitem__(self, item):
        return self.as_tuple()[item]

    def __iter__(self):
        return iter(self.as_tuple())

    def __repr__(self):
        return f"<Change: {str(self)}>"

    def __str__(self):
        parts = (str(x) if x is not None else '()' for x in self.as_tuple())
        return f"({', '.join(map(str, parts))})"


class DiffResult(object):
    """
    Result of a tree diff operation.
    """
    def __init__(self, base: tree.Node, other: tree.Node, mapping: DiffMapping,
                 changes: typing.Optional[DiffChanges] = None):
        self._base: tree.Node = base
        self._other: tree.Node = other
        self._mapping: DiffMapping = mapping
        self._changes: typing.Optional[DiffChanges] = changes
        self._reduced_changes: typing.Optional[DiffChanges] = None
        self._changes_by_node: typing.Dict[tree.Node, Change] = None

    @property
    def base(self) -> tree.Node:
        return self._base

    @property
    def other(self) -> tree.Node:
        return self._other

    @property
    def mapping(self) -> DiffMapping:
        return self._mapping

    @property
    def changes(self) -> DiffChanges:
        if self._changes is None:
            self._changes = list(calculate_changes(self.base, self.other, self.mapping))
        return self._changes

    @property
    def reduced_changes(self) -> DiffChanges:
        if self._reduced_changes is None:
            self._reduced_changes = list(reduce_changes(self.changes))
        return self._reduced_changes

    @property
    def changes_by_node(self):
        if self._changes_by_node is None:
            self._changes_by_node = {}
            # Build lookup table for changes per node
            for change in self.changes:
                assert change.base not in self._changes_by_node or change in self._changes_by_node.values()
                assert change.other not in self._changes_by_node or change in self._changes_by_node.values()

                if change.base is not None:
                    self._changes_by_node[change.base] = change
                if change.other is not None:
                    self._changes_by_node[change.other] = change
        return self._changes_by_node


def calculate_changes(base: tree.Node, other: tree.Node, mapping: DiffMapping) -> ChangesGenerator:
    """
    Calculates and yields the changes required to transform the base tree into the other tree.

    :param base: The base tree to calculate the changes for.
    :param other: The other tree to calculate the changes for.
    :param mapping: The calculated mapping between nodes of both trees.
    :return: Generator yielding the changes between the base tree and other tree.
    """
    for node in base.subtree():
        if node not in mapping.keys():
            yield Change(node, None, EditOperation.DELETE)
        elif node.name != mapping[node].name:
            yield Change(node, mapping[node], EditOperation.RENAME)
    for node in other.subtree():
        if node not in mapping.values():
            yield Change(None, node, EditOperation.INSERT)


def reduce_changes(changes: DiffChanges):
    """
    Reduces the changes to insert and delete operations.

    Contrary to what 'reduce' implicates, the number of changes grows by this operation.

    :param changes: The changes to reduce.
    :return: The reduced changes.
    """
    for change in changes:
        if change.op == EditOperation.RENAME:
            yield Change(change.base, None, EditOperation.DELETE)
            yield Change(None, change.other, EditOperation.INSERT)
        else:
            yield change


def tag_nodes(result: DiffResult) -> None:
    """
    Adds the change information to the IR nodes.
    """
    # Set mapping between nodes
    for base, other in result.mapping.items():
        base.mapping = other
        other.mapping = base

    # Set changed nodes
    for base, other, op in result.changes:
        if base is not None:
            base.is_changed = True
        if other is not None:
            other.is_changed = True
