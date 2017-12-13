import unittest

from checkmerge_llvm.analysis.types import Module, Function, Block


class ModuleTestCase(unittest.TestCase):
    """
    Tests the Module class
    """
    def setUp(self):
        self.module = Module('/home/user/code/file.c', 'file.c')

    def test_register_child(self):
        valid_child = Function('main', 'main')
        duplicate_child = Function('main', 'main')
        invalid_child = Block('block.entry', 'block.entry', valid_child)

        # Test valid child
        self.module.register_child(valid_child)

        self.assertEqual(1, len(self.module.functions))
        self.assertTrue(valid_child.key in self.module.functions)
        self.assertEqual(valid_child, self.module.functions[valid_child.key])

        # Test invalid child
        try:
            self.module.register_child(invalid_child)
            self.fail()
        except TypeError:
            pass

        self.assertEqual(1, len(self.module.functions))
        self.assertFalse(invalid_child.key in self.module.functions)

        # Test duplicate addition
        self.module.register_child(valid_child)

        try:
            self.module.register_child(duplicate_child)
            self.fail()
        except ValueError:
            pass

        self.assertEqual(1, len(self.module.functions))
