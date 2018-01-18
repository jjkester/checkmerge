import collections
import enum
import hashlib
import typing
import weakref
from functools import total_ordering

from cached_property import cached_property

from checkmerge.ir.metadata import Metadata, Location, Range


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
    #: Examples are function calls, typedefs, ...
    REFERENCE = 'R'

    #: Argument dependency: the source depends on the target as argument
    #: D1 is type dependent on D2 if D2 is an argument of D1.
    #: Examples are function declaration and calls, templates, ...
    ARGUMENT = 'A'

    #: Dependencies that do not fall in any of the other categories.
    OTHER = 'O'

    def __str__(self):
        return self._name_.capitalize()

    def is_memory_dependency(self):
        return self in (DependencyType.FLOW, DependencyType.ANTI, DependencyType.INPUT, DependencyType.OUTPUT)


# Generate a Dependency type with the named tuple factory
Dependency = collections.namedtuple('Dependency', ('node', 'type'))


@total_ordering
class IRNode(object):
    """
    Internal representation of an abstract syntax tree (AST) node.
    """
    def __init__(self, typ: str, label: typing.Optional[str] = None, ref: typing.Optional[str] = None,
                 parent: typing.Optional["IRNode"] = None,
                 children: typing.Optional[typing.List["IRNode"]] = None,
                 source_range: typing.Optional[Range] = None,
                 metadata: typing.Optional[typing.List[Metadata]] = None,
                 source_obj: typing.Optional[typing.Any] = None,
                 is_memory_operation: typing.Optional[bool] = None):
        """
        :param typ: The name of the type of the node.
        :param label: The string representation of the node.
        :param ref: The unique identifier of this node.
        :param parent: The parent node, or `None`.
        :param children: The children of this node.
        :param source_range: The location, start and end, in the source code of this node.
        :param metadata: The metadata of this node.
        :param source_obj: The original AST object for debug purposes.
        """
        # Initialize and set fields from arguments
        self.type: str = typ
        self.label: typing.Optional[str] = label
        self.ref: typing.Optional[str] = ref
        self._parent = None
        self.parent = parent
        self.source_obj: typing.Any = source_obj
        self.children: typing.List[IRNode] = children if children is not None else []
        self.source_range = source_range
        self.metadata: typing.List[Metadata] = metadata if metadata is not None else []
        self._is_memory_operation: typing.Optional[bool] = is_memory_operation

        # Check children and set parent
        for child in self.children:
            if child.parent is not None:
                raise ValueError("A child cannot be added if a parent is already set.")
            child.parent = self

        # Check parent and add as child
        if self.parent is not None and self not in self.parent.children:
            self.parent.children.append(self)

        # Initialize fields
        self._dependencies: typing.Set[Dependency] = set()
        self._reverse_dependencies: typing.Set[Dependency] = set()
        self._full_dependencies: typing.Optional[typing.Set[Dependency]] = None
        self._mapping: typing.Optional[IRNode] = None
        self._changed: typing.Optional[bool] = None

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
    def location(self) -> typing.Optional[Location]:
        if self.source_range is not None:
            return self.source_range.start
        return None

    @property
    def is_memory_operation(self) -> bool:
        if self._is_memory_operation is None:
            for dependency in set().union(self.dependencies, self.reverse_dependencies):
                if dependency.type.is_memory_dependency():
                    self._is_memory_operation = True
            self._is_memory_operation = True if self._is_memory_operation else False
        return self._is_memory_operation

    @property
    def dependencies(self) -> typing.Set[Dependency]:
        return self._dependencies

    @property
    def reverse_dependencies(self) -> typing.Set[Dependency]:
        return self._reverse_dependencies

    def add_dependencies(self, *dependencies: Dependency):
        for dependency in dependencies:
            self._dependencies.add(dependency)
            dependency.node._reverse_dependencies.add(Dependency(self, dependency.type))

    @property
    def mapping(self) -> typing.Optional["IRNode"]:
        return self._mapping

    @mapping.setter
    def mapping(self, value: typing.Optional["IRNode"]):
        assert value is not None
        assert self._mapping is None
        self._mapping = value

    @property
    def is_changed(self) -> bool:
        return bool(self._changed)

    @is_changed.setter
    def is_changed(self, value: bool):
        assert value is not None
        self._changed = value

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

    def recursive_dependencies(self, exclude: typing.Optional[typing.List["IRNode"]] = None,
                               limit: typing.Optional[typing.Callable[["IRNode"], bool]] = None,
                               recurse_memory_ops: bool = False) -> typing.Generator["IRNode", None, None]:
        if exclude is None:
            exclude = [self]

        dependencies = self.dependencies if limit is None else filter(limit, self.dependencies)

        for dependency in dependencies:
            exclude.append(dependency.node)
            yield dependency.node
            yield from dependency.node.recursive_dependencies(exclude, limit, recurse_memory_ops)

        if recurse_memory_ops and self.is_memory_operation:
            for child in self.subtree(include_self=False):
                yield child
                yield from child.recursive_dependencies(exclude, limit, recurse_memory_ops)

    def recursive_reverse_dependencies(self, exclude: typing.Optional[typing.List["IRNode"]] = None,
                                       limit: typing.Optional[typing.Callable[["IRNode"], bool]] = None,
                                       recurse_memory_ops: bool = False) -> typing.Generator["IRNode", None, None]:
        if exclude is None:
            exclude = [self]

        dependencies = self.reverse_dependencies if limit is None else filter(limit, self.reverse_dependencies)

        for dependency in dependencies:
            exclude.append(dependency.node)
            yield dependency.node
            yield from dependency.node.recursive_reverse_dependencies(exclude, limit, recurse_memory_ops)

        if recurse_memory_ops and self.is_memory_operation:
            for child in self.subtree(include_self=False):
                yield child
                yield from child.recursive_reverse_dependencies(exclude, limit, recurse_memory_ops)

    @property
    def full_dependencies(self) -> typing.Set["IRNode"]:
        if self._full_dependencies is None:
            self._full_dependencies = set().union(self.recursive_dependencies(), self.recursive_reverse_dependencies())
        return self._full_dependencies

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<{self.__class__.__name__} {str(self)}>"

    def __lt__(self, other):
        if not isinstance(other, IRNode):
            return NotImplemented
        return self.height < other.height

    def __le__(self, other):
        if not isinstance(other, IRNode):
            return NotImplemented
        return self.height <= other.height

    def __iter__(self):
        return iter(self.children)

    def __len__(self):
        return len(self.children)

    def __contains__(self, item):
        return item in self.children

    def __getitem__(self, item):
        if isinstance(item, tuple):
            if len(item) > 1:
                return self.children[item[0]][item[1:]]
            item = item[0]
        return self.children[item]
