import itertools
import typing

import bidict
import pylev3
import zss

from checkmerge.diff.base import DiffAlgorithm, DiffMapping, DiffResult
from checkmerge.ir import tree
from checkmerge.util.collections import PriorityList, exists


class GumTreeDiff(DiffAlgorithm):
    """
    Implementation of the GumTree tree diff algorithm [1]. This implementation is based on the algorithm description in
    [1] and not on the Java implementation [2].

    The `opt()` part of the algorithm is different from the algorithm used by the original authors so an existing Python
    implementation of an algorithm for the same purpose could be used.

    [1]: Falleri et al. Fine-grained and Accurate Source Code Differencing. 2014.
    [2]: https://github.com/GumTreeDiff/gumtree
    """

    def __init__(self, min_height: int = 2, min_dice: float = 0.3, max_size: int = 100):
        """
        Instantiates a new tree diff executor with the given configuration parameters. The default values have been
        taken from the Java implementation of the same algorithm.

        :param min_height: The minimum height of matched subtrees.
        :param min_dice: The minimum dice coefficient when nodes with non-matching subtrees can still be matched.
        :param max_size: The maximum size of a subtree to compute an edit script for.
        """
        super(GumTreeDiff, self).__init__()

        self.min_height = min_height
        self.min_dice = min_dice
        self.max_size = max_size

    def __call__(self, base: tree.Node, other: tree.Node, mapping: typing.Optional[DiffMapping] = None) -> DiffResult:
        """
        Runs the GumTree algorithm to find a mapping between the nodes of both trees.

        :param base: The base tree.
        :param other: The tree to compare.
        :param mapping: A mapping from nodes of the base tree to nodes of the other tree to start off with.
        :return: A mapping between nodes from the base tree to nodes from the other tree.
        """
        mapping = self.top_down(base, other)
        mapping = self.bottom_up(base, other, mapping)
        return DiffResult(base, other, mapping)

    def top_down(self, base: tree.Node, other: tree.Node, mapping: typing.Optional[DiffMapping] = None) -> DiffMapping:
        """
        Runs the GumTree top down phase on the given trees.

        The top down phase of the algorithm finds the largest isomorphic subtrees and maps these together.

        :param base: The base tree.
        :param other: The tree to compare.
        :param mapping: A mapping from nodes of the base tree to nodes of the other tree to start off with.
        :return: A mapping between nodes from the base tree to nodes from the other tree.
        """
        # List of nodes to evaluate ordered by their height (one for each tree)
        l1 = PriorityList(key=self.priority)
        l2 = PriorityList(key=self.priority)

        # Candidate mappings
        a: typing.List[typing.Tuple[tree.Node, tree.Node]] = []

        # Decided on mappings
        m: DiffMapping = bidict.bidict()

        # Add existing mappings
        if mapping is not None:
            for k, v in mapping.items():
                m[k] = v

        # Start with the root nodes
        l1.push(base)  # line 1
        l2.push(other)  # line 2

        # While there are large enough subtrees to compare, do comparison
        while l1 and l2 and min(l1.peek().height, l2.peek().height) >= self.min_height:  # line 3
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
                    if exists(other.subtree(), lambda tx: self.isomorphic(t1, tx) and tx != t2) or \
                            exists(base.subtree(), lambda tx: self.isomorphic(tx, t2) and tx != t1):  # Line 14
                        a.append((t1, t2))  # line 15
                    else:
                        # Because the trees are isomorphic walking them in the same order results in the correct
                        # mapping between the nodes
                        for n1, n2 in zip(t1.subtree(), t2.subtree()):
                            m[n1] = n2  # line 17

                # Add the unmapped subtrees to the queue
                for t in h1:  # line 18
                    if t not in map(lambda x: x[0], a) and t not in m:  # line 18
                        l1.open(t.children)  # line 18

                # Add the unmapped subtrees to the queue
                for t in h2:  # line 18
                    if t not in map(lambda x: x[1], a) and t not in m.inv:  # line 18
                        l2.open(t.children)  # line 18

        # Sort the candidate mappings on their dice coefficient
        a.sort(key=lambda x: self.dice(x[0].parent, x[1].parent, m), reverse=True)  # line 19

        # Add candidates in order to the mapping if the nodes are not mapped to ensure the best options are chosen
        for t1, t2 in a:  # line 20, 21
            if t1 not in m and t2 not in m.inv:  # line 23, 24
                for n1, n2 in filter(lambda x: self.isomorphic(*x) and x[0] not in m and x[1] not in m.inv, itertools.product(t1.subtree(), t2.subtree())):
                    m[n1] = n2  # line 22

        return m

    def bottom_up(self, base: tree.Node, other: tree.Node, m: DiffMapping) -> DiffMapping:
        """
        Runs the GumTree bottom up algorithm on the given trees. Expects a mapping from the top down phase as input.

        The bottom up phase tries to map nodes with a significant number of matching subtrees together.

        The mapping passed to this method will be mutated with the results for efficiency.

        :param base: The base tree.
        :param other: The tree to compare.
        :param m: A mapping between nodes from the base tree to nodes from the other tree. This is typically produced by
                  the top down phase algorithm.
        :return: A mapping between nodes from the base tree to nodes from the other tree.
        """
        # Iterate over unmatched nodes
        for t1 in filter(lambda x: x not in m, base.subtree(reverse=True)):  # line 1
            # Do steps if a child is matched
            if [c for c in t1.children if c in m]:
                # Select similar nodes based on dice coefficient
                t2s = filter(lambda y: y[1] not in m.values() and y[0] > self.min_dice and t1.type == y[1].type,
                             ((self.dice(t1, tx, m), tx) for tx in other.subtree(reverse=True)))  # line 2, 3

                # Choose best match
                t2 = max(t2s, default=(None, None))[1]  # line 2, 3

                # Store best match as mapping
                if t2 is not None:  # line 3
                    m[t1] = t2  # line 4

                    t1l = len(list(t1.subtree(include_self=False)))  # line 5
                    t2l = len(list(t2.subtree(include_self=False)))  # line 5

                    # Ensure we only do the following computation for suitably small trees
                    if max(t1l, t2l) < self.max_size:  # line 5
                        # Try to match even more nodes based on their edit distance
                        pairs = filter(lambda x: x[0] is not None and x[1] is not None, self.opt(t1, t2))  # line 6
                        for r1, r2 in pairs:  # line 7
                            if r1 not in m.keys() and r2 not in m.values() and r1.type == r2.type:  # line 8
                                m[r1] = r2  # line 9

        return m

    def opt(self, base: tree.Node, other: tree.Node) -> typing.List[typing.Tuple[tree.Node, tree.Node]]:
        """
        Runs the GumTree optimization algorithm on the given trees.

        The optimization algorithm tries to find mappings between nodes based on the edit distance.

        The Zhang-Shasha algorithm is used to calculate the edit distance with the Wagner-Fischer algorithm for the
        labels.
        """
        candidates = {}

        for t1, t2 in itertools.product(base.subtree(), other.subtree()):
            distance = zss.simple_distance(t1, t2, get_children=lambda n: n.children, get_label=lambda n: n.name,
                                           label_dist=pylev3.Levenshtein.wfi)

            if t1 not in candidates or candidates[t1][0] > distance:
                candidates[t1] = (distance, t2)

        return [(n, t[1]) for n, t in candidates.items()]

    @staticmethod
    def priority(t: tree.Node) -> int:
        """
        Key function for the priority list. Ensures the ordering of the nodes in the list is according to their height,
        with the largest height as the highest priority.

        :param t: The node to get the priority for.
        :return: The priority as integer.
        """
        return 0 - t.height

    @staticmethod
    def dice(t1: tree.Node, t2: tree.Node, mappings: typing.Dict[tree.Node, tree.Node]) -> float:
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
        common = len({d for d in d1 if mappings.get(d) in d2})
        return float(2 * common) / float(len(d1) + len(d2))

    @staticmethod
    def jaccard(t1: tree.Node, t2: tree.Node, mappings: typing.Dict[tree.Node, tree.Node]) -> float:
        d1 = set(t1.descendants)
        d2 = set(t2.descendants)
        common = len({d for d in d1 if mappings.get(d) in d2})
        try:
            return float(common) / float(len(d1) + len(d2) - common)
        except ZeroDivisionError:
            return 1.0

    @staticmethod
    def isomorphic(t1: tree.Node, t2: tree.Node) -> bool:
        """
        Returns whether two subtrees identified by nodes are isomorphic with respect to the GumTree algorithm.

        :param t1: The first subtree.
        :param t2: The second subtree.
        :return: Whether the given subtrees are isomorphic.
        """
        return t1.hash == t2.hash
