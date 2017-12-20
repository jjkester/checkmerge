import hashlib
import typing
import weakref

from cached_property import cached_property

from checkmerge.ir.metadata import Metadata


class IRNode(object):
    def __init__(self, typ: str, label: typing.Optional[str] = None, parent: typing.Optional["IRNode"] = None,
                 children: typing.Optional[typing.List["IRNode"]] = None,
                 metadata: typing.Optional[typing.List[Metadata]] = None,
                 source_obj: typing.Optional[typing.Any] = None):
        self.type: str = typ
        self.label: str = label
        self._parent = None
        self.parent: typing.Optional[IRNode] = parent
        self.source_obj: typing.Any = source_obj
        self.children: typing.List[IRNode] = children if children is not None else []
        self.metadata: typing.List[Metadata] = metadata if metadata is not None else []

        for child in self.children:
            if child.parent is not None:
                raise ValueError("A child cannot be added if a parent is already set.")
            child.parent = self

        if self.parent is not None and self not in self.parent.children:
            self.parent.children.append(self)

    @property
    def parent(self) -> typing.Optional["IRNode"]:
        if self._parent is None:
            return None
        return self._parent()

    @parent.setter
    def parent(self, value: typing.Optional["IRNode"]):
        if value is None:
            self._parent = None
        else:
            self._parent = weakref.ref(value)

    @cached_property
    def name(self):
        if self.label:
            return f"{self.type}: {self.label}"
        return f"{self.type}"

    @cached_property
    def is_leaf(self):
        return len(self.children) == 0

    @property
    def descendants(self) -> typing.Generator["IRNode", None, None]:
        for child in self.children:
            yield child

            for descendant in child.descendants:
                yield descendant

    @property
    def nodes(self) -> typing.Generator["IRNode", None, None]:
        yield self

        for descendant in self.descendants:
            yield descendant

    @cached_property
    def height(self) -> int:
        return self._height()

    def _height(self) -> int:
        if len(self.children) > 0:
            return max(map(IRNode._height, self.children)) + 1
        return 1

    @cached_property
    def hash(self) -> str:
        hasher = hashlib.blake2b()
        hasher.update(self._hash_str().encode())
        return hasher.hexdigest()

    def _hash_str(self) -> str:
        children = ''.join(map(IRNode._hash_str, self.children))
        return f"{{{self.type}@{self.label}|{children}}}"

    def subtree(self, include_self: bool = True, reverse: bool = False) -> typing.Generator["IRNode", None, None]:
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
