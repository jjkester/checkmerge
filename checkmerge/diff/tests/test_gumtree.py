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
        diff = GumTreeDiff(min_height=1, max_size=0)
        mapping = diff(self.t1, self.t2).mapping

        self.assertEqual(5, len(mapping))

        diff = GumTreeDiff(min_height=2, max_size=0)
        mapping = diff(self.t1, self.t2).mapping

        self.assertEqual(4, len(mapping))

    def test_max_size_threshold(self):
        diff = GumTreeDiff(min_height=1, max_size=0)
        mapping = diff(self.t1, self.t2).mapping

        self.assertEqual(5, len(mapping))

        diff = GumTreeDiff(min_height=1, max_size=8)
        mapping = diff(self.t1, self.t2).mapping

        self.assertEqual(7, len(mapping))


class EuclidGumTreeTestCase(unittest.TestCase):
    """
    Test case for the GumTree algorithm implementation using a tree based on the Euclidian algorithm.
    """
    def setUp(self):
        self.t1 = IRNode(typ="FunctionDef", label="gcd", children=[
            IRNode(typ="FunctionParam", label="a"),
            IRNode(typ="FunctionParam", label="b"),
            IRNode(typ="BasicBlock", children=[
                IRNode(typ="While", children=[
                    IRNode(typ="Condition", children=[
                        IRNode(typ="Operator", label="!=", children=[
                            IRNode(typ="VariableRef", label="a"),
                            IRNode(typ="VariableRef", label="b"),
                        ]),
                    ]),
                    IRNode(typ="BasicBlock", children=[
                        IRNode(typ="Conditional", children=[
                            IRNode(typ="Condition", children=[
                                IRNode(typ="Operator", label=">", children=[
                                    IRNode(typ="VariableRef", label="a"),
                                    IRNode(typ="VariableRef", label="b"),
                                ]),
                            ]),
                            IRNode(typ="BasicBlock", children=[
                                IRNode(typ="Assignment", label="a", children=[
                                    IRNode(typ="Operator", label="-", children=[
                                        IRNode(typ="VariableRef", label="a"),
                                        IRNode(typ="VariableRef", label="b"),
                                    ]),
                                ]),
                            ]),
                            IRNode(typ="BasicBlock", children=[
                                IRNode(typ="Assignment", label="b", children=[
                                    IRNode(typ="Operator", label="-", children=[
                                        IRNode(typ="VariableRef", label="b"),
                                        IRNode(typ="VariableRef", label="a"),
                                    ]),
                                ]),
                            ]),
                        ]),
                    ]),
                ]),
                IRNode(typ="Return", children=[
                    IRNode(typ="VariableRef", label="a"),
                ]),
            ]),
        ])

        self.t2 = IRNode(typ="FunctionDef", label="gcd", children=[
            IRNode(typ="FunctionParam", label="a"),
            IRNode(typ="FunctionParam", label="b"),
            IRNode(typ="BasicBlock", children=[
                IRNode(typ="While", children=[
                    IRNode(typ="Condition", children=[
                        IRNode(typ="Operator", label="!=", children=[
                            IRNode(typ="VariableRef", label="a"),
                            IRNode(typ="VariableRef", label="b"),
                        ]),
                    ]),
                    IRNode(typ="BasicBlock", children=[
                        IRNode(typ="Assignment", label="t", children=[
                            IRNode(typ="VariableRef", label="b"),
                        ]),
                        IRNode(typ="Assignment", label="b", children=[
                            IRNode(typ="Operator", label="%", children=[
                                IRNode(typ="VariableRef", label="a"),
                                IRNode(typ="VariableRef", label="b"),
                            ]),
                        ]),
                        IRNode(typ="Assignment", label="b", children=[
                            IRNode(typ="VariableRef", label="t"),
                        ]),
                    ]),
                ]),
                IRNode(typ="Return", children=[
                    IRNode(typ="VariableRef", label="a"),
                ]),
            ]),
        ])

        self.t3 = IRNode(typ="FunctionDef", label="gcd", children=[
            IRNode(typ="FunctionParam", label="a"),
            IRNode(typ="FunctionParam", label="b"),
            IRNode(typ="BasicBlock", children=[
                IRNode(typ="Condition", children=[
                    IRNode(typ="Operator", label="==", children=[
                        IRNode(typ="VariableRef", label="b"),
                        IRNode(typ="Value", label="0"),
                    ]),
                    IRNode(typ="BasicBlock", children=[
                        IRNode(typ="Return", children=[
                            IRNode(typ="VariableRef", label="a"),
                        ]),
                    ]),
                    IRNode(typ="BasicBlock", children=[
                        IRNode(typ="Return", children=[
                            IRNode("FunctionCall", label="gcd", children=[
                                IRNode("VariableRef", label="b"),
                                IRNode("Operator", label="%", children=[
                                    IRNode(typ="VariableRef", label="a"),
                                    IRNode(typ="VariableRef", label="b"),
                                ]),
                            ])
                        ]),
                    ]),
                ]),
            ]),
        ])

    def test_t1_t2(self):
        t1 = self.t1
        t2 = self.t2

        diff = GumTreeDiff()
        result = diff(t1, t2)
        mapping = set(result.mapping.items())

        # Top down equalities
        self.assertIn((t1, t2), mapping)  # FunctionDef: gcd
        self.assertIn((t1[0], t2[0]), mapping)  # FunctionParam: a
        self.assertIn((t1[1], t2[1]), mapping)  # FunctionParam: b
        self.assertIn((t1[2], t2[2]), mapping)  # BasicBlock
        self.assertIn((t1[2][0], t2[2][0]), mapping)  # While
        self.assertIn((t1[2][0][0], t2[2][0][0]), mapping)  # Condition
        self.assertIn((t1[2][0][0][0], t2[2][0][0][0]), mapping)  # Operator: !=
        self.assertIn((t1[2][0][0][0][0], t2[2][0][0][0][0]), mapping)  # VariableRef: a
        self.assertIn((t1[2][0][0][0][1], t2[2][0][0][0][1]), mapping)  # VariableRef: b
        self.assertIn((t1[2][0][1], t2[2][0][1]), mapping)  # BasicBlock
        self.assertIn((t1[2][1], t2[2][1]), mapping)  # Return
        self.assertIn((t1[2][1][0], t2[2][1][0]), mapping)  # VariableRef: a

        # Equal subtrees
        self.assertIn((t1[2][0][1][0][0][0], t2[2][0][1][1][0]), mapping)  # Operator: > / Operator: %
        self.assertIn((t1[2][0][1][0][1][0], t2[2][0][1][1]), mapping)  # Assignment: a / Assignment: b

        # Counts
        self.assertEqual(14, len(mapping))

    def test_t1_t2_relaxed(self):
        t1 = self.t1
        t2 = self.t2

        diff = GumTreeDiff(min_height=1)
        result = diff(t1, t2)
        mapping = set(result.mapping.items())

        # Top down equalities
        self.assertIn((t1, t2), mapping)  # FunctionDef: gcd
        self.assertIn((t1[0], t2[0]), mapping)  # FunctionParam: a
        self.assertIn((t1[1], t2[1]), mapping)  # FunctionParam: b
        self.assertIn((t1[2], t2[2]), mapping)  # BasicBlock
        self.assertIn((t1[2][0], t2[2][0]), mapping)  # While
        self.assertIn((t1[2][0][0], t2[2][0][0]), mapping)  # Condition
        self.assertIn((t1[2][0][0][0], t2[2][0][0][0]), mapping)  # Operator: !=
        self.assertIn((t1[2][0][0][0][0], t2[2][0][0][0][0]), mapping)  # VariableRef: a
        self.assertIn((t1[2][0][0][0][1], t2[2][0][0][0][1]), mapping)  # VariableRef: b
        self.assertIn((t1[2][0][1], t2[2][0][1]), mapping)  # BasicBlock
        self.assertIn((t1[2][1], t2[2][1]), mapping)  # Return
        self.assertIn((t1[2][1][0], t2[2][1][0]), mapping)  # VariableRef: a

        # Equal subtrees
        self.assertIn((t1[2][0][1][0][0][0], t2[2][0][1][1][0]), mapping)  # Operator: > / Operator: %
        self.assertIn((t1[2][0][1][0][1][0], t2[2][0][1][1]), mapping)  # Assignment: a / Assignment: b

        # Counts
        self.assertEqual(17, len(mapping))

    def test_t2_t3(self):
        t1 = self.t2
        t2 = self.t3

        diff = GumTreeDiff()
        result = diff(t1, t2)
        mapping = set(result.mapping.items())

        # Top down equalities
        self.assertIn((t1, t2), mapping)  # FunctionDef: gcd
        self.assertIn((t1[0], t2[0]), mapping)  # FunctionParam: a
        self.assertIn((t1[1], t2[1]), mapping)  # FunctionParam: b
        self.assertIn((t1[2], t2[2]), mapping)  # BasicBlock

        # Equal subtrees
        self.assertIn((t1[2][1], t2[2][0][1][0]), mapping)  # Return
        self.assertIn((t1[2][1][0], t2[2][0][1][0][0]), mapping)  # VariableRef: a
        self.assertIn((t1[2][0][1][1][0], t2[2][0][2][0][0][1]), mapping)  # Operator: %
        self.assertIn((t1[2][0][1][1][0][0], t2[2][0][2][0][0][1][0]), mapping)  # VariableRef: a
        self.assertIn((t1[2][0][1][1][0][1], t2[2][0][2][0][0][1][1]), mapping)  # VariableRef: b
        self.assertIn((t1[2][0][0][0][1], t2[2][0][0][0]), mapping)  # VariableRef: b

        # Counts
        self.assertEqual(10, len(mapping))

    def test_equal(self):
        t = self.t1
        diff = GumTreeDiff()
        result = diff(t, t)

        n = len(list(t.subtree()))

        self.assertEqual(n, len(result.mapping))
        self.assertEqual(n, len(set(result.mapping.keys())))  # Test uniqueness of keys
        self.assertEqual(n, len(set(result.mapping.values())))   # Test uniqueness of values
        self.assertEqual(0, len(result.changes))
