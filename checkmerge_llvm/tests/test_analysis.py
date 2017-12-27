import unittest

from checkmerge_llvm.analysis import AnalysisParser


class SimpleIRParseTestCase(unittest.TestCase):
    """
    Tests the reading and parsing of an IR file.
    """
    text = """
function.main:
  name: "main"
  module: "test/mini.ll"
  location: "/home/user/projects/checkmerge-llvm/test/mini.c:1:0"

  block.entry:
    - instruction.0:
        opcode: alloca
        location: ""
    - instruction.1:
        opcode: store
        location: ""
        dependencies:
          - "*instruction.0"
    - instruction.2:
        opcode: ret
        location: ":2:5"
    """
    data = {
        'function.main': {
            'name': "main",
            'module': "test/mini.ll",
            'location': "/home/user/projects/checkmerge-llvm/test/mini.c:1:0",
            'block.entry': [
                {'instruction.0': {
                    'opcode': 'alloca',
                    'location': '',
                }},
                {'instruction.1': {
                    'opcode': 'store',
                    'location': '',
                    'dependencies': ["*instruction.0"],
                }},
                {'instruction.2': {
                    'opcode': 'ret',
                    'location': ':2:5',
                }},
            ],
        },
    }

    def test_read(self):
        parser = AnalysisParser()
        data = parser._read(self.text)
        self.assertEqual(self.data, data)

    def test_parse(self):
        nodes = AnalysisParser.parse(self.text)
        self.assertEqual(4, len(nodes))
