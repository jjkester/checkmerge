import unittest

from checkmerge.ir.tree import IRNode, Dependency, DependencyType


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

    def test_dependencies(self):
        """Tests adding and querying dependencies."""
        # Add dependencies
        self.ll.add_dependencies(Dependency(self.lr, DependencyType.FLOW))
        self.ll.add_dependencies(Dependency(self.lr, DependencyType.REFERENCE))
        self.lrl.add_dependencies(Dependency(self.r, DependencyType.REFERENCE))
        self.rrl.add_dependencies(Dependency(self.lrl, DependencyType.REFERENCE))

        # Test dependencies
        self.assertEqual(set(), self.root.dependencies)
        self.assertEqual(set(), self.root.reverse_dependencies)
        self.assertEqual(set(), self.l.dependencies)
        self.assertEqual(set(), self.l.reverse_dependencies)
        self.assertEqual({Dependency(self.lr, DependencyType.FLOW), Dependency(self.lr, DependencyType.REFERENCE)},
                         self.ll.dependencies)
        self.assertEqual(set(), self.ll.reverse_dependencies)
        self.assertEqual(set(), self.lr.dependencies)
        self.assertEqual({Dependency(self.ll, DependencyType.FLOW), Dependency(self.ll, DependencyType.REFERENCE)},
                         self.lr.reverse_dependencies)
        self.assertEqual({Dependency(self.r, DependencyType.REFERENCE)}, self.lrl.dependencies)
        self.assertEqual({Dependency(self.rrl, DependencyType.REFERENCE)}, self.lrl.reverse_dependencies)
        self.assertEqual(set(), self.lrr.dependencies)
        self.assertEqual(set(), self.lrr.reverse_dependencies)
        self.assertEqual(set(), self.r.dependencies)
        self.assertEqual({Dependency(self.lrl, DependencyType.REFERENCE)}, self.r.reverse_dependencies)
        self.assertEqual(set(), self.rr.dependencies)
        self.assertEqual(set(), self.rr.reverse_dependencies)
        self.assertEqual({Dependency(self.lrl, DependencyType.REFERENCE)}, self.rrl.dependencies)
        self.assertEqual(set(), self.rrl.reverse_dependencies)

        # Test recursive dependencies
        self.assertEqual(set(), set(self.l.recursive_dependencies()))
        self.assertEqual({self.lrl, self.rrl}, set(self.r.recursive_reverse_dependencies()))
        self.assertEqual({self.lrl, self.lrr, self.r}, set(self.lr.recursive_dependencies(recurse_memory_ops=True)))

        # Test memory operation detection
        self.assertFalse(self.root.is_memory_operation)
        self.assertFalse(self.l.is_memory_operation)
        self.assertTrue(self.ll.is_memory_operation)
        self.assertTrue(self.lr.is_memory_operation)
        self.assertFalse(self.lrl.is_memory_operation)
        self.assertFalse(self.lrr.is_memory_operation)
        self.assertFalse(self.r.is_memory_operation)
        self.assertFalse(self.rr.is_memory_operation)
        self.assertFalse(self.rrl.is_memory_operation)
