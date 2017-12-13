import typing

import itertools

from checkmerge.diff.util import PriorityList
from checkmerge.ir import tree


class GumTreeDiff(object):
    def __init__(self, min_height: int):
        """
        :param min_height: The minimum height of matched subtrees.
        """
        self.min_height = min_height

    def top_down(self, base: tree.IRNode, other: tree.IRNode) -> typing.Dict[tree.IRNode, tree.IRNode]:
        """
        Runs the GumTree top down phase on the given trees.

        :param base: The base tree.
        :param other: The tree to compare.
        :return: A mapping between nodes from the base tree to the other tree.
        """
        # List of nodes to evaluate ordered by their height (one for each tree)
        l1 = PriorityList(key=self.priority)
        l2 = PriorityList(key=self.priority)

        # Candidate mappings
        a = []  # type: typing.List[typing.Tuple[tree.IRNode, tree.IRNode]]

        # Decided on mappings
        m = {}  # type: typing.Dict[tree.IRNode, tree.IRNode]

        # Start with the root nodes
        l1.push(base)  # line 1
        l2.push(other)  # line 2

        # While there are large enough subtrees to compare, do comparison
        while l1 and l2 and min(l1.peek().height, l2.peek().height) > self.min_height:  # line 3
            # Add the children of the larger subtree to the queue if the height is not equal
            if l1.peek().height > l2.peek().height:  # line 4, 5
                for t in l1.pop_many():  # line 6
                    l1.open(t.children)  # line 6
            elif l1.peek().height < l2.peek().height:  # line 4, 7
                for t in l2.pop_many():  # line 8
                    l2.open(t.children)  # line 8
            else:  # line 9
                # Retrieve all subtrees of equal height
                h1 = l1.pop_many()  # line 10
                h2 = l2.pop_many()  # line 11

                # Iterate over isomorphic pairs of subtrees
                for t1, t2 in filter(lambda x: self.isomorphic(*x), itertools.product(h1, h2)):  # line 12, 13
                    # If there are multiple candidates for a subtree, add these to the candidate set
                    # Otherwise add the subtrees and their children to the mappings.
                    if list(filter(lambda tx: self.isomorphic(t1, tx) and tx != t2, other.nodes)) \
                            or list(filter(lambda tx: self.isomorphic(tx, t2) and tx != t1, base.nodes)):  # line 14
                        a.append((t1, t2))  # line 15
                    else:
                        # TODO This loop is inefficient but guaranteed to have the desired effect.
                        for n1, n2 in filter(lambda x: self.isomorphic(*x), itertools.product(t1.nodes, t2.nodes)):
                            m[n1] = n2  # line 17

                # Add the unmapped subtrees to the queue
                for t in h1:  # line 18
                    if t not in map(lambda x: x[0], a) and t not in m.keys():  # line 18
                        l1.open(t.children)  # line 18

                # Add the unmapped subtrees to the queue
                for t in h2:  # line 18
                    if t not in map(lambda x: x[1], a) and t not in m.values():  # line 18
                        l2.open(t.children)  # line 18

        # Sort the candidate mappings on their dice coefficient
        a.sort(key=lambda x: self.dice(x[0].parent, x[1].parent, m), reverse=True)  # line 19

        # Add candidates in order to the mapping if the nodes are not mapped to ensure the best options are chosen
        for t1, t2 in a:  # line 20, 21
            if t1 not in m.keys() and t2 not in m.values():  # line 23, 24
                for n1, n2 in filter(lambda x: self.isomorphic(*x), itertools.product(t1.nodes, t2.nodes)):
                    m[n1] = n2  # line 17

        return m

    @staticmethod
    def priority(t: tree.IRNode) -> int:
        """
        Key function for the priority list. Ensures the ordering of the nodes in the list is according to their height,
        with the largest height as the highest priority.

        :param t: The node to get the priority for.
        :return: The priority as integer.
        """
        return 0 - t.height

    @staticmethod
    def dice(t1: tree.IRNode, t2: tree.IRNode, mappings: typing.Dict[tree.IRNode, tree.IRNode]) -> float:
        """
        The dice function calculates a ratio of common descendants between two nodes given existing mappings between
        nodes. The dice coefficient ranges between 0 and 1. A value of 0 indicates that no descendants match while 1
        indicates that the subtrees match.

        :param t1: The first node.
        :param t2: The second node.
        :param mappings: The mappings between nodes of t1 (keys) and t2 (values).
        :return: The dice coefficient given the two subtrees and the mappings.
        """
        d1 = set(t1.descendants)
        d2 = set(t2.descendants)
        common = len({d for d in d1 if mappings[t1] in d2})
        return float(2 * common) / float(len(d1) + len(d2))

    @staticmethod
    def isomorphic(t1: tree.IRNode, t2: tree.IRNode) -> bool:
        """
        Returns whether two subtrees identified by nodes are isomorphic with respect to the GumTree algorithm.

        :param t1: The first subtree.
        :param t2: The second subtree.
        :return: Whether the given subtrees are isomorphic.
        """
        return t1.hash == t2.hash
