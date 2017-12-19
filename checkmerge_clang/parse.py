import tempfile
import typing

import clang.cindex as clang

from checkmerge import parse, ir


class ClangParser(parse.Parser):
    """
    A CheckMerge parser using the Clang compiler.

    As Clang only works with files it is recommended to use parsing from file for efficiency reasons. The other parse
    methods have been implemented to use a temporary file. Therefore, using `parse_stream` with a source file would mean
    a lot of unnecessary IO overhead.
    """
    def parse_str(self, val: str) -> typing.List[ir.IRNode]:
        # Create temporary file to work with
        with tempfile.NamedTemporaryFile() as f:
            # Write string to file
            f.write(val)

            # Parse from file
            return self.parse_file(f.name)

    def parse_stream(self, stream: typing.IO) -> typing.List[ir.IRNode]:
        # Create temporary file to work with
        with tempfile.NamedTemporaryFile() as f:
            # Write string to file
            f.write(stream.read())

            # Parse from file
            return self.parse_file(f.name)

    def parse_file(self, path: str) -> typing.List[ir.IRNode]:
        index = clang.Index.create()

        try:
            tu = index.parse(path=path)
        except clang.TranslationUnitLoadError:
            raise parse.ParseError(f"Unable to parse")

        return [self._parse_clang_node(tu.cursor)]

    def _parse_clang_node(self, cursor: clang.Cursor, parent: typing.Optional[ir.IRNode] = None) -> ir.IRNode:
        # Get location
        location = ir.Location(cursor.location.file, cursor.location.line, cursor.location.column)

        # Build metadata
        metadata: typing.List[ir.Metadata] = [location]

        # Build node
        node = ir.IRNode(
            typ=cursor.kind.name,
            label=cursor.spelling,
            parent=parent,
            metadata=metadata,
            source_obj=cursor,
        )

        # Parse children and add to node
        for child in cursor.get_children():
            self._parse_clang_node(child, node)

        return node
