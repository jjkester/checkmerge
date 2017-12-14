import hashlib
import typing

from checkmerge.ir.metadata import Metadata


class IRNode(object):
    def __init__(self, typ: str, label: typing.Optional[str] = None, parent: typing.Optional["IRNode"] = None,
                 children: typing.Optional[typing.List["IRNode"]] = None,
                 metadata: typing.Optional[typing.List[Metadata]] = None,
                 source_obj: typing.Optional[typing.Any] = None):
        self.type = typ
        self.label = label
        self.parent = parent
        self.source_obj = source_obj
        self.children = children if children is not None else []  # type: typing.List[IRNode]
        self.metadata = metadata if metadata is not None else []  # type: typing.List[Metadata]

        for child in self.children:
            if child.parent is not None:
                raise ValueError("A child cannot be added if a parent is already set.")
            child.parent = self

        if self.parent is not None and self not in self.parent.children:
            self.parent.children.append(self)

    @property
    def name(self):
        if self.label:
            return f"{self.type}: {self.label}"
        return f"{self.type}"

    @property
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

    @property
    def height(self) -> int:
        return self._height()

    def _height(self) -> int:
        if len(self.children) > 0:
            return max(map(IRNode._height, self.children)) + 1
        return 1

    @property
    def hash(self) -> str:
        hasher = hashlib.blake2b()
        hasher.update(self._hash_str().encode())
        return hasher.hexdigest()

    def _hash_str(self) -> str:
        children = ''.join(map(IRNode._hash_str, self.children))
        return f"{{{self.type}@{self.label}|{children}}}"

    def subtree(self, reverse: bool = False) -> typing.Generator["IRNode", None, None]:
        return self._bottom_up_subtree() if reverse else self._top_down_subtree()

    def _top_down_subtree(self):
        yield self

        for child in self.children:
            for node in child._top_down_subtree():
                yield node

    def _bottom_up_subtree(self):
        for child in self.children:
            for node in child._bottom_up_subtree():
                yield node

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
