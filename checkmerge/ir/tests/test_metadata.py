import random
import unittest

from checkmerge.ir.metadata import Location


class LocationTestCase(unittest.TestCase):
    """
    Tests for the Location class.
    """
    file = '/home/user/code/file.c'
    line = random.randint(1, 1000)
    column = random.randint(1, 80)

    def setUp(self):
        self.string = f"{self.file}:{self.line}:{self.column}"

    def test_parse(self):
        """
        Tests parsing a string location into a Location object.
        """
        location = Location.parse(self.string)

        # Tests
        self.assertEqual(self.file, location.file)
        self.assertEqual(self.line, location.line)
        self.assertEqual(self.column, location.column)

    def test_equality(self):
        """
        Tests the (in)equality of two Location objects.
        """
        base_location = Location(self.file, self.line, self.column)
        equal_location = Location(self.file, self.line, self.column)
        different_file_location = Location(self.file + 'pp', self.line, self.column)
        different_line_location = Location(self.file, ((self.line + 1) * 2) % 1000, self.column)
        different_column_location = Location(self.file, self.line, self.column + 10)

        # Test equality
        self.assertTrue(base_location == equal_location)
        self.assertTrue(equal_location == base_location)

        # Test inequality
        self.assertTrue(base_location != different_file_location)
        self.assertFalse(base_location == different_file_location)
        self.assertFalse(base_location == different_line_location)
        self.assertFalse(base_location == different_column_location)

    def test_is_line(self):
        """
        Tests full line detection.
        """
        location = Location(self.file, self.line, self.column)
        line_location = Location(self.file, self.line, 0)

        self.assertFalse(location.is_line)
        self.assertTrue(line_location.is_line)

    def test_comparable(self):
        """
        Tests comparing two Location objects.
        """
        location = Location(self.file, self.line, self.column)

        before = [
            Location(self.file, self.line - 1, self.column + 10),
            Location(self.file, self.line, self.column - 1),
        ]

        after = [
            Location(self.file, self.line + 1, self.column - 10),
            Location(self.file, self.line, self.column + 1),
        ]

        # Only run this test if there is a file, otherwise the locs should be equal (so this test would fail)
        if location.file:
            before.append(Location('/home/user/code/afile.c', self.line, self.column))
            after.append(Location('/home/user/code/zfile.c', self.line, self.column))

        for other in before:
            self.assertLess(other, location)
            self.assertLessEqual(other, location)
            self.assertGreater(location, other)
            self.assertGreaterEqual(location, other)

        for other in after:
            self.assertGreater(other, location)
            self.assertGreaterEqual(other, location)
            self.assertLess(location, other)
            self.assertLessEqual(location, other)


class NoFileLocationTestCase(LocationTestCase):
    """
    Tests for the Location class with an undefined file.
    """
    file = ''
