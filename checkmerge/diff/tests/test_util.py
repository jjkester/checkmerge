import unittest

from checkmerge.diff.util import exists


class ExistsTestCase(unittest.TestCase):
    def test_list(self):
        """Tests the behavior of `exists` when used with lists."""
        self.assertFalse(exists(list()))
        self.assertTrue(exists([1, 2, 3]))
        self.assertTrue(exists([None]))

    def test_set(self):
        """Tests the behavior of `exists` when used with sets."""
        self.assertFalse(exists(set()))
        self.assertTrue(exists({1, 2, 3}))
        self.assertTrue(exists({1, 1, 1}))
        self.assertTrue(exists({None}))

    def test_dict(self):
        """Tests the behavior of `exists` when used with dictionaries."""
        empty = dict()
        nonempty = {1: 'one', 2: 'two'}
        
        self.assertFalse(exists(empty))
        self.assertTrue(exists(nonempty))
        
        self.assertFalse(exists(empty.keys()))
        self.assertFalse(exists(empty.values()))
        self.assertFalse(exists(empty.items()))
        
        self.assertTrue(exists(nonempty.keys()))
        self.assertTrue(exists(nonempty.values()))
        self.assertTrue(exists(nonempty.items()))

    def test_iterator(self):
        self.assertFalse(exists(iter(list())))
        self.assertTrue(exists(iter([1, 2, 3])))
        self.assertTrue(exists(iter([None])))

        iterator = iter([1, 2, 3])
        exists(iterator)

        self.assertEqual([1, 2, 3], list(iterator))
