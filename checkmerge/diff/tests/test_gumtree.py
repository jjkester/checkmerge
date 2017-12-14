import unittest
from copy import deepcopy

from checkmerge.diff.gumtree import GumTreeDiff
from checkmerge.ir.tree import IRNode


class GumTreeTestCase(unittest.TestCase):
    def setUp(self):
        self.t1 = IRNode("Sequence", children=[
            IRNode("While", children=[
                IRNode("Operator", "!=", children=[
                    IRNode("Variable", "b"),
                    IRNode("Value", "0"),
                ]),
                IRNode("Conditional", children=[
                    IRNode("Operator", ">", children=[
                        IRNode("Variable", "a"),
                        IRNode("Variable", "b"),
                    ]),
                    IRNode("Assignment", children=[
                        IRNode("Variable", "a"),
                        IRNode("Operator", "-", children=[
                            IRNode("Variable", "a"),
                            IRNode("Variable", "b"),
                        ]),
                    ]),
                    IRNode("Assignment", children=[
                        IRNode("Variable", "b"),
                        IRNode("Operator", "-", children=[
                            IRNode("Variable", "b"),
                            IRNode("Variable", "a"),
                        ]),
                    ]),
                ]),
            ]),
            IRNode("Return", children=[
                IRNode("Variable", "a"),
            ]),
        ])

        self.t2 = IRNode("Sequence", children=[
            IRNode("While", children=[
                IRNode("Operator", "!=", children=[
                    IRNode("Variable", "b"),
                    IRNode("Value", "0"),
                ]),
                IRNode("Conditional", children=[
                    IRNode("Operator", "<", children=[
                        IRNode("Variable", "a"),
                        IRNode("Variable", "b"),
                    ]),
                    IRNode("Assignment", children=[
                        IRNode("Variable", "a"),
                        IRNode("Operator", "-", children=[
                            IRNode("Variable", "a"),
                            IRNode("Variable", "b"),
                        ]),
                    ]),
                    IRNode("Assignment", children=[
                        IRNode("Variable", "b"),
                        IRNode("Operator", "-", children=[
                            IRNode("Variable", "b"),
                            IRNode("Variable", "a"),
                        ]),
                    ]),
                ]),
            ]),
            IRNode("Return", children=[
                IRNode("Operator", "+", children=[
                    IRNode("Value", "1"),
                    IRNode("Variable", "a"),
                ]),
            ]),
        ])

    def test_top_down_equal(self):
        """Tests the top down phase algorithm with two equal trees."""
        diff = GumTreeDiff()
        t1 = self.t1
        t2 = deepcopy(self.t1)

        mapping = diff.top_down(t1, t2)

        self.assertEqual(21, len(mapping))
        self.assertEqual(t2, mapping[t1])

        t1_nodes = list(t1.descendants)
        t2_nodes = list(t2.descendants)

        self.assertTrue(len(t1_nodes) == len(t2_nodes))

        # Test if the nodes are mapped correctly
        for i in range(0, len(t1_nodes)):
            self.assertEqual(t2_nodes[i].hash, mapping[t1_nodes[i]].hash)
            self.assertEqual(t2_nodes[i].type, mapping[t1_nodes[i]].type)
            self.assertEqual(t2_nodes[i].label, mapping[t1_nodes[i]].label)
            self.assertEqual(len(t2_nodes[i].children), len(mapping[t1_nodes[i]].children))

    def test_top_down_unequal(self):
        """Tests the top down phase algorithm with two slightly different trees."""
        diff = GumTreeDiff()
        t1 = self.t1
        t2 = self.t2

        mapping = diff.top_down(t1, t2)

        expected_mapping = {
            t1[0][1][1]: t2[0][1][1],
            t1[0][1][1][0]: t2[0][1][1][0],
            t1[0][1][1][1]: t2[0][1][1][1],
            t1[0][1][1][1][0]: t2[0][1][1][1][0],
            t1[0][1][1][1][1]: t2[0][1][1][1][1],
            t1[0][1][2]: t2[0][1][2],
            t1[0][1][2][0]: t2[0][1][2][0],
            t1[0][1][2][1]: t2[0][1][2][1],
            t1[0][1][2][1][0]: t2[0][1][2][1][0],
            t1[0][1][2][1][1]: t2[0][1][2][1][1],
        }

        self.assertEqual(len(expected_mapping), len(mapping))

        hash_mapping = {k.hash: v.hash for k, v in mapping.items()}
        expected_hash_mapping = {k.hash: v.hash for k, v in expected_mapping.items()}

        self.assertEqual(expected_hash_mapping, hash_mapping)

    def test_complete_equal(self):
        """Tests the GumTree algorithm with two equal trees."""
        diff = GumTreeDiff()
        t1 = self.t1
        t2 = deepcopy(self.t1)

        mapping = diff(t1, t2)

        self.assertEqual(21, len(mapping))
        self.assertEqual(t2, mapping[t1])

        t1_nodes = list(t1.descendants)
        t2_nodes = list(t2.descendants)

        self.assertTrue(len(t1_nodes) == len(t2_nodes))

        # Test if the nodes are mapped correctly
        for i in range(0, len(t1_nodes)):
            self.assertEqual(t2_nodes[i].hash, mapping[t1_nodes[i]].hash)
            self.assertEqual(t2_nodes[i].type, mapping[t1_nodes[i]].type)
            self.assertEqual(t2_nodes[i].label, mapping[t1_nodes[i]].label)
            self.assertEqual(len(t2_nodes[i].children), len(mapping[t1_nodes[i]].children))

    def test_complete_unequal(self):
        """Tests the GumTree algorithm with two slightly different trees."""
        diff = GumTreeDiff()
        t1 = self.t1
        t2 = deepcopy(self.t1)

        # Change label to trigger difference
        t2.label = "(different)"

        mapping = diff(t1, t2)

        t1_nodes = list(t1.nodes)
        t2_nodes = list(t2.nodes)

        expected_mapping = {t1_nodes[i]: t2_nodes[i] for i in range(len(t1_nodes))}
        # Remove "Return" subtree - not matched due to height of 2
        del expected_mapping[t1[1]]
        del expected_mapping[t1[1][0]]

        self.assertEqual(len(expected_mapping), len(mapping))

        hash_mapping = {k.hash: v.hash for k, v in mapping.items()}
        expected_hash_mapping = {k.hash: v.hash for k, v in expected_mapping.items()}

        self.assertEqual(expected_hash_mapping, hash_mapping)
