import collections
import enum
import hashlib
import typing
import weakref

from cached_property import cached_property

from checkmerge.ir.metadata import Metadata, Location


class DependencyType(enum.Enum):
    """
    A type of dependency.
    """
    #: Control dependency: the target conditionally guards the execution of the source.
    #: S2 is control dependent on S1 if the execution of S2 depends on the result of S1.
    CONTROL = 'C'

    #: Flow (memory) dependency: the target writes memory that the source reads (read after write).
    #: S2 is flow dependent on S1 if and only if S1 modifies a resource that S2 reads and S1 precedes S2 in execution.
    FLOW = 'MF'

    #: Anti (memory) dependency: the target reads memory that the source writes (write after read).
    #: S2 is antidependent on S1 if and only if S1 reads a resource that S2 modifies and S1 precedes S2 in execution.
    ANTI = 'MA'

    #: Output (memory) dependency: the target and source modify the same resource (write after write).
    #: S2 is output dependent on S1 if and only if S1 and S2 modify the same resource and S1 precedes S2 in execution.
    OUTPUT = 'MO'

    #: Input (memory) dependency: the target and source read the same resource (read after read).
    #: S2 is input dependent on S1 if and only if S1 and S2 read the same resource and S1 precedes S2 in execution.
    INPUT = 'MI'

    #: Reference dependency: the source refers to a named entity defined by the target.
    #: S is reference dependent on N if S refers to the named entity N.
    #: Examples are type references, function calls, ...
    REFERENCE = 'R'

    #: Dependencies that do not fall in any of the other categories.
    OTHER = 'O'


# Generate a Dependency type with the named tuple factory
Dependency: typing.Type[typing.Tuple["IRNode", DependencyType]] = collections.namedtuple('Dependency', ('node', 'type'))


class IRNode(object):
    """
    Internal representation of an abstract syntax tree (AST) node.
    """
    def __init__(self, typ: str, label: typing.Optional[str] = None, parent: typing.Optional["IRNode"] = None,
                 children: typing.Optional[typing.List["IRNode"]] = None,
                 location: typing.Optional[Location] = None,
                 metadata: typing.Optional[typing.List[Metadata]] = None,
                 source_obj: typing.Optional[typing.Any] = None):
        """
        :param typ: The name of the type of the node.
        :param label: The string representation of the node.
        :param parent: The parent node, or `None`.
        :param children: The children of this node.
        :param location: The location in the source code of this node.
        :param metadata: The metadata of this node.
        :param source_obj: The original AST object for debug purposes.
        """
        # Initialize and set fields from arguments
        self.type: str = typ
        self.label: str = label
        self._parent = None
        self.parent: typing.Optional[IRNode] = parent
        self.source_obj: typing.Any = source_obj
        self.children: typing.List[IRNode] = children if children is not None else []
        self.location = location
        self.metadata: typing.List[Metadata] = metadata if metadata is not None else []

        # Check children and set parent
        for child in self.children:
            if child.parent is not None:
                raise ValueError("A child cannot be added if a parent is already set.")
            child.parent = self

        # Check parent and add as child
        if self.parent is not None and self not in self.parent.children:
            self.parent.children.append(self)

        # Initialize fields
        self.dependencies: typing.Set[Dependency] = set()

    @property
    def parent(self) -> typing.Optional["IRNode"]:
        """Getter for the parent node that unwraps the weak reference."""
        if callable(self._parent):
            return self._parent()
        return self._parent

    @parent.setter
    def parent(self, value: typing.Optional["IRNode"]):
        """Setter for the parent node that uses a weak reference to allow garbage collection."""
        if value is None:
            self._parent = None
        else:
            self._parent = weakref.ref(value)

    @property
    def name(self):
        """The name of this node, which is a combination of the type and the label."""
        if self.label:
            return f"{self.type}: {self.label}"
        return f"{self.type}"

    @property
    def is_root(self):
        """Whether this node is the root of a tree."""
        return self._parent is None

    @property
    def is_leaf(self):
        """Whether this node is a leaf of the tree."""
        return len(self.children) == 0

    @property
    def descendants(self) -> typing.Generator["IRNode", None, None]:
        """Generator for the descendants of this node. Yields the descendants top-down in a depth-first manner."""
        for child in self.children:
            yield child

            for descendant in child.descendants:
                yield descendant

    @property
    def nodes(self) -> typing.Generator["IRNode", None, None]:
        """Generator for the nodes in this subtree. Yields the nodes top-down in a depth-first manner."""
        yield self

        for descendant in self.descendants:
            yield descendant

    @cached_property
    def height(self) -> int:
        """The height of the subtree."""
        return self._height()

    def _height(self) -> int:
        if len(self.children) > 0:
            return max(map(IRNode._height, self.children)) + 1
        return 1

    @cached_property
    def hash(self) -> str:
        """A hash of this subtree. Allows for finding equal subtrees. This hash does NOT uniquely identify this node."""
        hasher = hashlib.blake2b()
        hasher.update(self._hash_str().encode())
        return hasher.hexdigest()

    def _hash_str(self) -> str:
        children = ''.join(map(IRNode._hash_str, self.children))
        return f"{{{self.type}@{self.label}|{children}}}"

    def subtree(self, include_self: bool = True, reverse: bool = False) -> typing.Generator["IRNode", None, None]:
        """
        Returns a generator which yields the nodes in the subtree identified by this node. Allows for the subtree to be
        walked top-down or bottom-up (both depth-first). Optionally includes the current node in the iteration.

        :param include_self: Whether to include this node in the iteration.
        :param reverse: Whether to walk the subtree bottom-up instead of top-down.
        :return: A generator which yields the nodes in this subtree.
        """
        return self._bottom_up_subtree(include_self) if reverse else self._top_down_subtree(include_self)

    def _top_down_subtree(self, include_self: bool = True):
        if include_self:
            yield self

        for child in self.children:
            for node in child._top_down_subtree():
                yield node

    def _bottom_up_subtree(self, include_self: bool = True):
        for child in self.children:
            for node in child._bottom_up_subtree():
                yield node

        if include_self:
            yield self

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<{self.__class__.__name__} {str(self)}>"

    def __lt__(self, other):
        if isinstance(other, IRNode):
            return self.height < other.height
        return super(IRNode, self).__lt__(other)

    def __le__(self, other):
        if isinstance(other, IRNode):
            return self.height <= other.height
        return super(IRNode, self).__le__(other)

    def __gt__(self, other):
        if isinstance(other, IRNode):
            return self.height > other.height
        return super(IRNode, self).__gt__(other)

    def __ge__(self, other):
        if isinstance(other, IRNode):
            return self.height >= other.height
        return super(IRNode, self).__ge__(other)

    def __iter__(self):
        return iter(self.children)

    def __len__(self):
        return len(self.children)

    def __contains__(self, item):
        return item in self.children

    def __getitem__(self, item):
        return self.children[item]
