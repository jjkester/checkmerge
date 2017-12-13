import pprint
import typing

from checkmerge_llvm.analysis import types

# Define stream type
Stream = typing.Union[typing.AnyStr, typing.IO]


class IRPrinter(object):
    """
    Printer for the analysis IR.
    """
    def __init__(self, stream: Stream = None):
        self._stream = stream

    def print(self, node: types.AnalysisNode):
        printer = pprint.PrettyPrinter(indent=2, stream=self._stream)
        printer.pprint(self.transform(node))

    def transform(self, node: types.AnalysisNode) -> typing.Dict[str, typing.Dict]:
        def _extract(x):
            return self.transform(x).items()

        if isinstance(node, types.Module):
            return {
                self.format_module(node): {
                    k: v for (k, v), in map(_extract, node.functions.values())
                }
            }
        elif isinstance(node, types.Function):
            return {
                self.format_function(node): {
                    k: v for (k, v), in map(_extract, node.blocks.values())
                }
            }
        elif isinstance(node, types.Block):
            return {
                self.format_block(node): {
                    k: v for (k, v), in map(_extract, node.instructions.values())
                }
            }
        elif isinstance(node, types.Instruction):
            return {
                self.format_instruction(node): {}
            }
        return {}

    @staticmethod
    def format_module(module: types.Module) -> str:
        """
        Formats a module for print.
        """
        return "Module <{uid}>".format(
            uid=module.uid,
        )
    
    @staticmethod
    def format_function(function: types.Function) -> str:
        """
        Formats a function for print.
        """
        return "Function <{uid}>".format(
            uid=function.uid,
        )
    
    @staticmethod
    def format_block(block: types.Block) -> str:
        """
        Formats a block for print.
        """
        return "Block <{uid}>".format(
            uid=block.uid,
        )

    @staticmethod
    def format_instruction(instruction: types.Instruction) -> str:
        """
        Formats an instruction for print.
        """
        return "Instruction <{uid}>".format(
            uid=instruction.uid,
        )
