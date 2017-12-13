import typing

from checkmerge.ir import tree


# Diff algorithm types
DiffMapping = typing.Dict[tree.IRNode, tree.IRNode]


class DiffAlgorithm(object):
    """
    Base class for diff algorithms.
    """
    def __call__(self, base: tree.IRNode, other: tree.IRNode) -> DiffMapping:
        """
        Runs the diff algorithm to calculate a mapping between nodes of the base tree and the other tree.

        :param base: The base tree.
        :param other: The tree to compare.
        :return: A mapping from nodes of the base tree to nodes of the other tree.
        """
        raise NotImplementedError()
