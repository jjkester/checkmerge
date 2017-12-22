import unittest

from checkmerge.util.collections import PriorityList


class PriorityListTestCase(unittest.TestCase):
    """
    Test case for the PriorityList data structure.
    """
    def setUp(self):
        self.data = [10, 8, 9, 3, -1, 8, 3, 4]

    def test_without_key_func(self):
        """Tests a priority list without using a custom key function."""
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
        """Tests a priority list with a custom key function."""
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
