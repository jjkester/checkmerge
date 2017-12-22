import unittest

from checkmerge.util.scope import Scope


class ScopeTestCase(unittest.TestCase):
    """
    Test case for the Scope data structure.
    """
    def setUp(self):
        self.bottom = Scope()
        self.middle = Scope(parent=self.bottom)
        self.top = Scope(parent=self.middle)

        self.bottom.update(foo=10, bar=20, baz=30)
        self.middle.update(bar=21, qux=41)
        self.top.update(baz=32, quux=52)

        self.scope = self.top

    def test_get(self):
        """Tests the recursive get method of a Scope."""
        self.assertEqual(10, self.scope.get('foo'))
        self.assertEqual(21, self.scope.get('bar'))
        self.assertEqual(32, self.scope.get('baz'))
        self.assertEqual(41, self.scope.get('qux'))
        self.assertEqual(52, self.scope.get('quux'))
        self.assertEqual(None, self.scope.get('quuux'))
        self.assertEqual(10, self.scope.get('foo', default=9))
        self.assertEqual(9, self.scope.get('quuux', default=9))

        self.assertEqual(30, self.middle.get('baz'))
        self.assertEqual(None, self.bottom.get('qux'))

        self.assertEqual(10, self.scope['foo'])
        self.assertEqual(21, self.scope['bar'])
        self.assertEqual(32, self.scope['baz'])
        self.assertEqual(41, self.scope['qux'])

        try:
            self.scope['quuux']
        except KeyError:
            pass
        else:
            self.fail()

    def test_set(self):
        """Tests setting items on a scope."""
        self.scope['foo'] = 13
        self.scope.update(qux=43)

        self.assertEqual(13, self.scope['foo'])
        self.assertEqual(43, self.scope['qux'])
        self.assertEqual(10, self.middle['foo'])
        self.assertEqual(41, self.middle['qux'])

    def test_del(self):
        """Tests deleting items from a scope."""
        del self.scope['baz']

        # Expected KeyError when deleting bar, fail if no error
        try:
            del self.scope['bar']
        except KeyError:
            pass
        else:
            self.fail()

        self.assertEqual(30, self.scope.get('baz'))
        self.assertEqual(21, self.scope.get('bar'))

    def test_len(self):
        """Tests the length of a scope."""
        self.assertEqual(3, len(self.bottom))
        self.assertEqual(4, len(self.middle))
        self.assertEqual(5, len(self.top))

        self.scope['quuux'] = 63

        self.assertEqual(3, len(self.bottom))
        self.assertEqual(4, len(self.middle))
        self.assertEqual(6, len(self.top))

    def test_keys(self):
        """Tests the keys of a scpe."""
        self.assertEqual({'foo', 'bar', 'baz'}, self.bottom.keys())
        self.assertEqual({'foo', 'bar', 'baz', 'qux'}, self.middle.keys())
        self.assertEqual({'foo', 'bar', 'baz', 'qux', 'quux'}, self.top.keys())
