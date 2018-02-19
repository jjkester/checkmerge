import enum
import os
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

    def __call__(self, base: tree.Node, other: tree.Node, mapping: typing.Optional[DiffMapping] = None) -> "DiffResult":
        """
        Runs the diff algorithm to calculate a mapping between nodes of the base tree and the other tree.

        :param base: The base tree.
        :param other: The tree to compare.
        :param mapping: A mapping from nodes of the base tree to nodes of the other tree to start off with.
        :return: A mapping from nodes of the base tree to nodes of the other tree.
        """
        raise NotImplementedError()

    def __repr__(self):
        return f"<{self.__class__.__name__}>"


class EditOperation(enum.Enum):
    """
    Kinds of operations for transforming a tree.
    """
    INSERT = '+'
    DELETE = '-'
    RENAME = '~'

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return f"<EditOperation {self}>"


class Change(object):
    """
    A change found by the diff algorithm.
    """
    __slots__ = ('base', 'other', 'op')

    def __init__(self, base: typing.Optional[tree.Node], other: typing.Optional[tree.Node], op: EditOperation):
        """
        :param base: The changed node in the base tree.
        :param other: The changed node in the other tree.
        :param op: The edit operation.
        """
        assert not (base is None and other is None)
        assert op is not None

        self.base = base
        self.other = other
        self.op = op

    @property
    def sort_key(self):
        node = self.base or self.other
        if node is not None:
            return os.path.basename(node.location.file), node.location.line, node.location.column
        return ()

    def as_tuple(self) -> typing.Tuple[tree.Node, tree.Node, EditOperation]:
        return self.base, self.other, self.op

    def __getitem__(self, item):
        return self.as_tuple()[item]

    def __iter__(self):
        return iter(self.as_tuple())

    def __repr__(self):
        return f"<Change {str(self)}>"

    def __str__(self):
        parts = (str(x) if x is not None else '()' for x in self.as_tuple())
        return f"({', '.join(parts)})"


class DiffResult(object):
    """
    Result of a tree diff operation.
    """
    __slots__ = ('_base', '_other', '_mapping', '_changes', '_reduced_changes', '_changes_by_node')

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
        """The base tree."""
        return self._base

    @property
    def other(self) -> tree.Node:
        """The other tree."""
        return self._other

    @property
    def mapping(self) -> DiffMapping:
        """The mapping from nodes of the base tree to nodes of the other tree."""
        return self._mapping

    @property
    def changes(self) -> DiffChanges:
        """The changes extracted from nodes."""
        if self._changes is None:
            self._changes = list(calculate_changes(self.base, self.other, self.mapping))
        return self._changes

    @property
    def changes_by_node(self):
        """Dictionary for looking up a change by a node."""
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


class MergeDiffResult(DiffResult):
    """
    Special cased diff result for merges.
    """
    def __init__(self, base: tree.Node, other: tree.Node, ancestor: tree.Node, base_result: DiffResult,
                 other_result: DiffResult, two_way_result: typing.Optional[DiffResult] = None):
        # Build combined mapping
        mapping = combine_mappings(base_result.mapping, other_result.mapping)

        # If there is a two-way diff result, add additional mappings if none of the nodes is already mapped
        if two_way_result is not None:
            for base_node, other_node in two_way_result.mapping.items():
                if base_node not in mapping.keys() and other_node not in mapping.values():
                    mapping[base_node] = other_node

        # Super init
        super(MergeDiffResult, self).__init__(base, other, mapping)

        # Set additional properties
        self._ancestor = ancestor
        self._base_result = base_result
        self._other_result = other_result

    @property
    def ancestor(self) -> tree.Node:
        """The ancestor tree."""
        return self._ancestor

    @property
    def base_mapping(self) -> DiffMapping:
        """The mapping from nodes of the ancestor tree to nodes of the base tree."""
        return self._base_result.mapping

    @property
    def other_mapping(self) -> DiffMapping:
        """The mapping from nodes of the ancestor tree to nodes of the other tree."""
        return self._other_result.mapping

    @property
    def base_changes(self) -> DiffChanges:
        """The changes in the base version with respect to the ancestor."""
        return self._base_result.changes

    @property
    def other_changes(self) -> DiffChanges:
        """The changes in the other version with respect to the ancestor."""
        return self._other_result.changes

    @property
    def base_changes_by_node(self):
        return self._base_result.changes_by_node

    @property
    def other_changes_by_node(self):
        return self._other_result.changes_by_node


def combine_mappings(base_mapping: DiffMapping, other_mapping: DiffMapping) -> DiffMapping:
    """
    Combines the given mappings by matching the common key nodes. Returns a mapping from the values of the first mapping
    to the values of the second mapping for values with the same key.

    Requires the keys of both mappings to be of the same tree.

    :param base_mapping: Mapping from a common ancestor to the base version.
    :param other_mapping: Mapping from a common ancestor to the other version.
    :return: Mapping from the base version to the other version.
    """
    mapping = {}
    for key in set(base_mapping.keys()).intersection(set(other_mapping.keys())):
        mapping[base_mapping[key]] = other_mapping[key]
    return mapping


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
