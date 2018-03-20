import enum
import hashlib
import typing
import weakref
from functools import total_ordering

from checkmerge.ir.metadata import Location, Metadata, Range


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

    def __repr__(self):
        return f"<DependencyType {self}>"

    def __str__(self):
        return self._name_.capitalize()

    def is_memory_dependency(self) -> bool:
        """
        :return: Whether this dependency is a memory dependency.
        """
        return self in (DependencyType.FLOW, DependencyType.ANTI, DependencyType.INPUT, DependencyType.OUTPUT)


class Dependency(object):
    """
    Dependency of a node on another node with a certain type. By default, the node that is depended on is referenced
    in this object.

    A dependency can be a reverse dependency, in which case the node referenced in this object is the node that depends
    on the object holding this dependency.

    In general, the node that holds this object is not referenced in this object.

    The reference to the node is weak to allow for proper garbage collection. Do not expect to use only a dependency
    object to keep a reference to a certain node.
    """
    __slots__ = ('_node', 'type', 'reverse')

    def __init__(self, node: "Node", typ: "DependencyType", reverse: bool = False):
        """
        :param node: The node that is depended on.
        :param typ: The type of dependency.
        :param reverse: Whether this is a reverse dependency.
        """
        self._node = None
        self.node = node
        self.type = typ
        self.reverse = reverse

    @property
    def node(self) -> typing.Optional["Node"]:
        if callable(self._node):
            return self._node()
        return self._node

    @node.setter
    def node(self, value: "Node") -> None:
        assert value is not None
        self._node = weakref.ref(value)

    def as_tuple(self) -> typing.Tuple["Node", DependencyType]:
        """Returns this dependency in a 2-tuple representation."""
        return self.node, self.type

    def __eq__(self, other):
        if isinstance(other, Dependency):
            return self.as_tuple() == other.as_tuple()
        return super(Dependency, self).__eq__(other)

    def __hash__(self):
        return hash(self.as_tuple())

    def __getitem__(self, item):
        return self.as_tuple()[item]

    def __iter__(self):
        return iter(self.as_tuple())

    def __repr__(self):
        return f"<Dependency {self}>"

    def __str__(self):
        return f"{self.type} {self.node}"


@total_ordering
class Node(object):
    """
    Internal representation of an abstract syntax tree (AST) node.

    References to the children of a node are strong, while references to the parent are weak to allow for proper garbage
    collection. It is therefore important to keep a reference to the root of the tree.
    """
    __slots__ = ('type', 'label', 'ref', '_parent', 'children', 'source_range', 'metadata', '_is_memory_operation',
                 '_dependencies', '_reverse_dependencies', '_mapping', '_changed', '_height', '_hash', '_hash_str',
                 '_root', '__weakref__')

    def __init__(self, typ: str, label: typing.Optional[str] = None, ref: typing.Optional[str] = None,
                 parent: typing.Optional["Node"] = None,
                 children: typing.Optional[typing.List["Node"]] = None,
                 source_range: typing.Optional[Range] = None,
                 metadata: typing.Optional[typing.List[Metadata]] = None,
                 is_memory_operation: typing.Optional[bool] = None):
        """
        :param typ: The name of the type of the node.
        :param label: The string representation of the node.
        :param ref: The unique identifier of this node for cross-reference purposes.
        :param parent: The parent node, or `None`.
        :param children: The children of this node.
        :param source_range: The location, start and end, in the source code of this node.
        :param metadata: The metadata of this node.
        :param is_memory_operation: Overrides the automatic detection of memory operations for analysis purposes.
        """
        # Initialize and set fields from arguments
        self.type: str = typ
        self.label: typing.Optional[str] = label
        self.ref: typing.Optional[str] = ref
        self._parent = None
        self.parent = parent
        self.children: typing.List[Node] = children if children is not None else []
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
        self._mapping: typing.Optional[Node] = None
        self._changed: typing.Optional[bool] = None
        self._height = None
        self._hash = None
        self._hash_str = None
        self._root = None

    @property
    def parent(self) -> typing.Optional["Node"]:
        """Getter for the parent node that unwraps the weak reference."""
        if callable(self._parent):
            return self._parent()
        return self._parent

    @parent.setter
    def parent(self, value: typing.Optional["Node"]):
        """Setter for the parent node that uses a weak reference to allow garbage collection."""
        if value is None:
            self._parent = None
        else:
            self._parent = weakref.ref(value)

    @property
    def root(self) -> "Node":
        """The root node of the tree."""
        if self._root is None:
            self._root = self.parent.root if self.parent is not None else self
        return self._root

    @property
    def location(self) -> typing.Optional[Location]:
        """The location of the first character of this node."""
        if self.source_range is not None:
            return self.source_range.start
        return None

    @property
    def is_memory_operation(self) -> bool:
        """
        Returns whether this operation is a memory operation. This is automatically detected by analyzing the
        dependencies of a node. A node is a memory operation if it is on either end of a memory dependency.

        This can be overridden by setting the `is_memory_operation` flag in the constructor of a node. This should be
        done for memory operations that are not automatically detected by the parser, for example, a return statement.

        :return: Whether this node represents a memory operation.
        """
        if self._is_memory_operation is None:
            for dependency in set().union(self.dependencies, self.reverse_dependencies):
                if dependency.type.is_memory_dependency():
                    self._is_memory_operation = True
                    break
            self._is_memory_operation = True if self._is_memory_operation else False
        return self._is_memory_operation

    @property
    def is_definition(self) -> bool:
        """
        Returns whether this node is a definition. This is automatically detected by analyzing the dependencies of a
        node. A node is a definition if it has reference dependencies to it.

        :return: Whether this node represents a definition.
        """
        for dependency in self.reverse_dependencies:
            if dependency.type == DependencyType.REFERENCE:
                return True
        return False

    @property
    def dependencies(self) -> typing.Set[Dependency]:
        """The dependencies of this node."""
        return self._dependencies

    @property
    def reverse_dependencies(self) -> typing.Set[Dependency]:
        """The dependencies on this node."""
        return self._reverse_dependencies

    def add_dependencies(self, *dependencies: Dependency) -> None:
        """
        Adds one or more dependencies to this node. Reverse dependencies are added automatically.

        :param dependencies: The dependencies to add.
        """
        for dependency in dependencies:
            self._dependencies.add(dependency)
            dependency.node._reverse_dependencies.add(Dependency(self, dependency.type, reverse=True))

    @property
    def mapping(self) -> typing.Optional["Node"]:
        """
        Returns the node in another tree that is mapped to this node, if any.

        Mappings are only known if the diff result was applied to the tree.
        """
        return self._mapping

    @mapping.setter
    def mapping(self, value: typing.Optional["Node"]) -> None:
        """Sets the mapping between two nodes."""
        assert value is not None
        assert self._mapping is None
        self._mapping = value

    @property
    def is_changed(self) -> bool:
        """Whether this node has been changed. This is only known if the diff result was applied to the tree."""
        return bool(self._changed)

    @is_changed.setter
    def is_changed(self, value: bool):
        """Sets the change status of this node."""
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
    def descendants(self) -> typing.Generator["Node", None, None]:
        """Generator for the descendants of this node. Yields the descendants top-down in a depth-first manner."""
        for child in self.children:
            yield child
            yield from child.descendants

    @property
    def nodes(self) -> typing.Generator["Node", None, None]:
        """Generator for the nodes in this subtree. Yields the nodes top-down in a depth-first manner."""
        yield self
        yield from self.descendants

    @property
    def height(self) -> int:
        """The height of the subtree."""
        if self._height is None:
            self._height = self._get_height()
        return self._height

    def _get_height(self) -> int:
        """Calculates the height of the subtree recursively."""
        if len(self.children) > 0:
            return max(map(lambda n: n.height, self.children)) + 1
        return 1

    @property
    def hash(self) -> str:
        """A hash of this subtree. Allows for finding equal subtrees. This hash does NOT uniquely identify this node."""
        if self._hash is None:
            hasher = hashlib.blake2b()
            hasher.update(self._get_hash_str().encode())
            self._hash = hasher.hexdigest()
        return self._hash

    def _get_hash_str(self) -> str:
        """Calculates the string used for calculating the hash recursively."""
        if self._hash_str is None:
            children = ''.join(map(Node._get_hash_str, self.children))
            self._hash_str = f"{{{self.type}@{self.label}|{children}}}"
        return self._hash_str

    def subtree(self, include_self: bool = True, reverse: bool = False) -> typing.Generator["Node", None, None]:
        """
        Returns a generator which yields the nodes in the subtree identified by this node. Allows for the subtree to be
        walked top-down or bottom-up (both depth-first). Optionally includes the current node in the iteration.

        :param include_self: Whether to include this node in the iteration.
        :param reverse: Whether to walk the subtree bottom-up instead of top-down.
        :return: A generator which yields the nodes in this subtree.
        """
        return self._bottom_up_subtree(include_self) if reverse else self._top_down_subtree(include_self)

    def _top_down_subtree(self, include_self: bool = True):
        """Generator for traversing the subtree top-down."""
        if include_self:
            yield self

        for child in self.children:
            for node in child._top_down_subtree():
                yield node

    def _bottom_up_subtree(self, include_self: bool = True):
        """Generator for traversing the subtree bottom-up."""
        for child in self.children:
            for node in child._bottom_up_subtree():
                yield node

        if include_self:
            yield self

    def recursive_dependencies(self, exclude: typing.Optional[typing.List["Node"]] = None,
                               limit: typing.Optional[typing.Callable[[Dependency], bool]] = None,
                               recurse_memory_ops: bool = False) -> typing.Generator["Node", None, None]:
        """
        Generator for the recursive dependencies of this node. The recursive dependencies form the dependency graph
        from this node.

        :param exclude: The nodes to not traverse. Used for recursive calls to prevent following cycles.
        :param limit: Callable accepting a dependency and returning a boolean for filtering which dependencies should be
                      traversed.
        :param recurse_memory_ops: Whether to include all child nodes of a memory operation.
        :return: A generator yielding the nodes in the dependency graph from this node.
        """
        if exclude is None:
            exclude = [self]

        dependencies = self.dependencies if limit is None else filter(limit, self.dependencies)

        for dependency in dependencies:
            exclude.append(dependency.node)
            yield dependency.node
            yield from dependency.node.recursive_dependencies(exclude, limit, recurse_memory_ops)

        if recurse_memory_ops and self.is_memory_operation:
            for child in self.subtree(include_self=False):
                exclude.append(child)
                yield child
                yield from child.recursive_dependencies(exclude, limit, recurse_memory_ops)

    def recursive_reverse_dependencies(self, exclude: typing.Optional[typing.List["Node"]] = None,
                                       limit: typing.Optional[typing.Callable[[Dependency], bool]] = None,
                                       recurse_memory_ops: bool = False) -> typing.Generator["Node", None, None]:
        """
        Generator for the recursive reverse dependencies of this node. The recursive reverse dependencies form the
        dependency graph to this node.

        :param exclude: The nodes to not traverse. Used for recursive calls to prevent following cycles.
        :param limit: Callable accepting a dependency and returning a boolean for filtering which dependencies should be
                      traversed.
        :param recurse_memory_ops: Whether to include all child nodes of a memory operation.
        :return: A generator yielding the nodes in the dependency graph to this node.
        """
        if exclude is None:
            exclude = [self]

        dependencies = self.reverse_dependencies if limit is None else filter(limit, self.reverse_dependencies)

        for dependency in dependencies:
            exclude.append(dependency.node)
            yield dependency.node
            yield from dependency.node.recursive_reverse_dependencies(exclude, limit, recurse_memory_ops)

        if recurse_memory_ops and self.is_memory_operation:
            for child in self.subtree(include_self=False):
                exclude.append(child)
                yield child
                yield from child.recursive_reverse_dependencies(exclude, limit, recurse_memory_ops)

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<Node {self}>"

    def __lt__(self, other):
        if not isinstance(other, Node):
            return NotImplemented
        return self.height < other.height

    def __le__(self, other):
        if not isinstance(other, Node):
            return NotImplemented
        return self.height <= other.height

    def __iter__(self):
        return iter(self.children)

    def __len__(self):
        return len(self.children)

    def __bool__(self):
        return True

    def __contains__(self, item):
        return item in self.children

    def __getitem__(self, item):
        if isinstance(item, tuple):
            if len(item) > 1:
                return self.children[item[0]][item[1:]]
            item = item[0]
        return self.children[item]
