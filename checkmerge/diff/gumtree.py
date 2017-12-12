import typing

import itertools

from checkmerge.diff.util import exists, PriorityList
from checkmerge.ir import tree


class GumTreeDiff(object):
    pass


class GumTreeTopDown(object):
    def __init__(self, min_height: int):
        self.min_height = min_height

    def __call__(self, base: tree.IRNode, other: tree.IRNode) -> typing.Dict[tree.IRNode, tree.IRNode]:
        l1 = PriorityList(key=self.priority)
        l2 = PriorityList(key=self.priority)
        a = []  # type: typing.List[typing.Tuple[tree.IRNode, tree.IRNode]]
        m = {}  # type: typing.Dict[tree.IRNode, tree.IRNode]

        l1.push(base)  # line 1
        l2.push(other)  # line 2

        while l1 and l2 and min(l1.peek().height, l2.peek().height) > self.min_height:  # line 3
            if l1.peek().height > l2.peek().height:  # line 4, 5
                for t in l1.pop_many():  # line 6
                    l1.open(t.children)  # line 6
            elif l1.peek().height < l2.peek().height:  # line 4, 7
                for t in l2.pop_many():  # line 8
                    l2.open(t.children)  # line 8
            else:  # line 9
                h1 = l1.pop_many()  # line 10
                h2 = l2.pop_many()  # line 11

                for t1, t2 in filter(lambda x: self.isomorphic(*x), itertools.product(h1, h2)):  # line 12, 13
                    if list(filter(lambda tx: self.isomorphic(t1, tx) and tx != t2, other.nodes)) \
                            or list(filter(lambda tx: self.isomorphic(tx, t2) and tx != t1, base.nodes)):  # line 14
                        a.append((t1, t2))  # line 15
                    else:
                        for n1, n2 in filter(lambda x: self.isomorphic(*x), itertools.product(t1.nodes, t2.nodes)):
                            m[n1] = n2  # line 17

                for t in h1:  # line 18
                    if t not in map(lambda x: x[0], a) and t not in m.keys():  # line 18
                        l1.open(t.children)  # line 18

                for t in h2:  # line 18
                    if t not in map(lambda x: x[1], a) and t not in m.values():  # line 18
                        l2.open(t.children)  # line 18

        a.sort(key=lambda x: self.dice(x[0].parent, x[1].parent, m))  # line 19

        for t1, t2 in a:  # line 20, 21
            if t1 not in m.keys() and t2 not in m.values():  # line 23, 24
                for n1, n2 in filter(lambda x: self.isomorphic(*x), itertools.product(t1.nodes, t2.nodes)):
                    m[n1] = n2  # line 17

        return m

    @staticmethod
    def priority(t: tree.IRNode):
        return 0 - t.height

    @staticmethod
    def dice(t1: tree.IRNode, t2: tree.IRNode, mappings: typing.Dict[tree.IRNode, tree.IRNode]) -> float:
        d1 = set(t1.descendants)
        d2 = set(t2.descendants)
        common = len({d for d in d1 if mappings[t1] in d2})
        return float(2 * common) / float(len(d1) + len(d2))

    @staticmethod
    def isomorphic(t1: tree.IRNode, t2: tree.IRNode) -> bool:
        return t1.hash == t2.hash

    @classmethod
    def rmap(cls, t1: tree.IRNode, t2: tree.IRNode, mappings: typing.Dict[tree.IRNode, tree.IRNode]) -> None:
        mappings[t1] = t2

        for c1, c2 in filter(lambda x: cls.isomorphic(*x), itertools.product(t1.children, t2.children)):
            cls.rmap(c1, c2, mappings)
