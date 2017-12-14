import unittest

from checkmerge.ir.tree import IRNode


class IRNodeTestCase(unittest.TestCase):
    def setUp(self):
        self.root = IRNode("root", label="2")
        self.l = IRNode("child", label="7", parent=self.root)
        self.ll = IRNode("child", label="2", parent=self.l)
        self.lr = IRNode("child", label="6", parent=self.l)
        self.lrl = IRNode("child", label="5", parent=self.lr)
        self.lrr = IRNode("child", label="11", parent=self.lr)
        self.r = IRNode("child", label="5", parent=self.root)
        self.rr = IRNode("child", label="9", parent=self.r)
        self.rrl = IRNode("child", label="4", parent=self.rr)

    def test_descendants(self):
        """Tests the generation of the descendants of a node."""
        self.assertEqual([], list(self.rrl.descendants))
        self.assertEqual([self.rr, self.rrl], list(self.r.descendants))
        self.assertEqual([self.l, self.ll, self.lr, self.lrl, self.lrr, self.r, self.rr, self.rrl],
                         list(self.root.descendants))

    def test_nodes(self):
        """Tests the generation of the node list of a node."""
        self.assertEqual([self.lrl], list(self.lrl.nodes))
        self.assertEqual([self.lr, self.lrl, self.lrr], list(self.lr.nodes))
        self.assertTrue(self.root in self.root.nodes)

    def test_height(self):
        """Tests the calculation of the height of a node."""
        self.assertEqual(1, self.ll.height)
        self.assertEqual(3, self.l.height)
        self.assertEqual(4, self.root.height)

    def test_hash(self):
        """Tests the calculation of a hash of a node."""
        self.assertEqual(self.root.hash, self.root.hash)
        self.assertNotEqual(self.l.hash, self.r.hash)
        self.assertEqual(self.rrl.hash, IRNode("child", label="4").hash)

    def test_subtree(self):
        """Tests the top down walking of subtrees."""
        self.assertEqual([self.rrl], list(self.rrl.subtree()))
        self.assertEqual([self.rrl], list(self.rrl.subtree(reverse=True)))
        self.assertEqual([self.root, self.l, self.ll, self.lr, self.lrl, self.lrr, self.r, self.rr, self.rrl],
                         list(self.root.subtree()))
        self.assertEqual([self.ll, self.lrl, self.lrr, self.lr, self.l, self.rrl, self.rr, self.r, self.root],
                         list(self.root.subtree(reverse=True)))