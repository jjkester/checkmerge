import unittest

from checkmerge.ir.parse import IRParser


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
            'name': 'main',
            'module': 'test/mini.ll',
            'location': '/home/user/projects/checkmerge-llvm/test/mini.c:1:0',
            'block.entry': [
                {'instruction.0': {
                    'opcode': 'alloca',
                    'location': '',
                }},
                {'instruction.1': {
                    'opcode': 'store',
                    'location': '',
                    'dependencies': [
                        '*instruction.0',
                    ],
                }},
                {'instruction.2': {
                    'opcode': 'ret',
                    'location': ':2:5',
                }},
            ],
        },
    }

    def test_read(self):
        parser = IRParser()
        data = parser._read(self.text)
        self.assertEqual(self.data, data)

    def test_get_module(self):
        parser = IRParser()
        module_name = 'file.c'

        module = parser._get_module(module_name)

        self.assertEqual(module_name, module.name)
        self.assertEqual(1, len(parser._modules))

        module2 = parser._get_module(module_name)

        self.assertEqual(module, module2)
        self.assertEqual(1, len(parser._modules))
