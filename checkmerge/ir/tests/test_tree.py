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
        self.assertEqual([], list(self.rrl.descendants))
        self.assertEqual([self.rr, self.rrl], list(self.r.descendants))
        self.assertEqual([self.l, self.ll, self.lr, self.lrl, self.lrr, self.r, self.rr, self.rrl],
                         list(self.root.descendants))

    def test_nodes(self):
        self.assertEqual([self.lrl], list(self.lrl.nodes))
        self.assertEqual([self.lr, self.lrl, self.lrr], list(self.lr.nodes))
        self.assertTrue(self.root in self.root.nodes)

    def test_height(self):
        self.assertEqual(1, self.ll.height)
        self.assertEqual(3, self.l.height)
        self.assertEqual(4, self.root.height)

    def test_hash(self):
        self.assertEqual(self.root.hash, self.root.hash)
        self.assertNotEqual(self.l.hash, self.r.hash)
        self.assertEqual(self.rrl.hash, IRNode("child", label="4").hash)
