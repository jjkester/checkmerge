import unittest

from checkmerge.diff.util import exists, PriorityList


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
        """Tests the behaviour of `exists` when used with iterators."""
        self.assertFalse(exists(iter(list())))
        self.assertTrue(exists(iter([1, 2, 3])))
        self.assertTrue(exists(iter([None])))

        iterator = iter([1, 2, 3])
        exists(iterator)

        self.assertEqual([1, 2, 3], list(iterator))


class PriorityListTestCase(unittest.TestCase):
    def setUp(self):
        self.data = [10, 8, 9, 3, -1, 8, 3, 4]

    def test_without_key_func(self):
        pl = PriorityList()

        # Add data
        for d in self.data:
            pl.push(d)

        # Tests
        self.assertEqual(len(self.data), len(pl))
        self.assertEqual(-1, pl.pop())
        self.assertEqual(3, pl.pop())
        self.assertEqual(3, pl.pop())
        self.assertEqual([4], pl.pop_many())
        self.assertEqual([8, 8], pl.pop_many())
        self.assertEqual(9, pl.pop())
        self.assertTrue(pl)
        self.assertEqual(10, pl.pop())
        self.assertFalse(pl)
        self.assertEqual(0, len(pl))

    def test_with_key_func(self):
        # Key function for reverse order
        pl = PriorityList(key=lambda x: 0 - x)

        # Add data
        for d in self.data:
            pl.push(d)

        # Tests
        self.assertEqual(len(self.data), len(pl))
        self.assertEqual(10, pl.pop())
        self.assertEqual(9, pl.pop())
        self.assertEqual([8, 8], pl.pop_many())
        self.assertEqual([4], pl.pop_many())
        self.assertEqual(3, pl.pop())
        self.assertEqual(3, pl.pop())
        self.assertTrue(pl)
        self.assertEqual(-1, pl.pop())
        self.assertFalse(pl)
        self.assertEqual(0, len(pl))
