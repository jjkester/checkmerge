import unittest

from checkmerge.diff.gumtree import GumTreeDiff
from checkmerge.ir.tree import IRNode


class OriginalGumTreeTestCase(unittest.TestCase):
    """
    Test case for the GumTree algorithm implementation that was taken from the original Java implementation of GumTree.
    """
    def setUp(self):
        self.t1 = IRNode(typ="0", label="a", children=[
            IRNode(typ="0", label="e", children=[
                IRNode(typ="2", label="f"),
            ]),
            IRNode(typ="0", label="b", children=[
                IRNode(typ="0", label="c"),
                IRNode(typ="0", label="d"),
            ]),
            IRNode(typ="0", label="g"),
        ])

        self.t2 = IRNode(typ="0", label="z", children=[
            IRNode(typ="0", label="b", children=[
                IRNode(typ="0", label="c"),
                IRNode(typ="0", label="d"),
            ]),
            IRNode(typ="1", label="h", children=[
                IRNode(typ="0", label="e", children=[
                    IRNode(typ="2", label="y"),
                ]),
            ]),
            IRNode(typ="0", label="g"),
        ])

    def test_min_height_threshold(self):
        diff = GumTreeDiff(min_height=0, max_size=0)
        mapping = diff(self.t1, self.t2)

        self.assertEqual(5, len(mapping))

        diff = GumTreeDiff(min_height=1, max_size=0)
        mapping = diff(self.t1, self.t2)

        self.assertEqual(4, len(mapping))

    def test_max_size_threshold(self):
        diff = GumTreeDiff(min_height=0, max_size=0)
        mapping = diff(self.t1, self.t2)

        self.assertEqual(5, len(mapping))

        diff = GumTreeDiff(min_height=0, max_size=8)
        mapping = diff(self.t1, self.t2)

        self.assertEqual(6, len(mapping))
