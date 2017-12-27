import collections
import os
import queue
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
        # Create index for parsing
        index = clang.Index.create()

        # Check if file exists
        if not os.path.isfile(path):
            raise parse.ParseError(f"The file {path} does not exist.")

        # Try if parsing the code is successful
        try:
            tu = index.parse(path=path)
        except clang.TranslationUnitLoadError:
            raise parse.ParseError(f"Unable to parse {path}. Run your compiler and check for errors.")

        return [self._walk_ast(tu.cursor)]

    def _walk_ast(self, cursor: clang.Cursor) -> ir.IRNode:
        """
        Iterates over the AST to build an IR tree.

        :param cursor: The cursor for the root node of the AST.
        """
        # Queue
        walk_queue = queue.LifoQueue()

        # Mapping of declarations (functions, types, ...)
        mapping: typing.Dict[clang.Cursor, ir.IRNode] = {}

        # Temporary dependency storage
        DependencyCache = typing.Dict[ir.IRNode, typing.Set[typing.Tuple[clang.Cursor, ir.DependencyType]]]
        dependencies: DependencyCache = collections.defaultdict(list)

        # Add first element to queue
        walk_queue.put((cursor, None))

        root = None

        # Walk the AST and create the IR tree
        while True:
            try:
                cursor, parent = walk_queue.get()

                # Build IR node from cursor
                node = self._parse_clang_node(cursor, parent)

                # Set as root if appropriate
                if root is None:
                    root = node

                # Add reference dependencies if appropriate
                dependencies[node].update(((d, ir.DependencyType.REFERENCE) for d in self._get_references(cursor)))

                # Add arguments of calls and function definitions as dependency
                dependencies[node].update(((d, ir.DependencyType.ARGUMENT) for d in self._get_arguments(cursor)))

                # Map cursor to node for dependency resolving
                mapping[cursor] = node

                # Add children to queue
                for child in cursor.get_children():
                    walk_queue.put((child, node))
            except queue.Empty:
                # Break out of loop when the queue is empty
                break

        # Resolve dependencies
        for node, deps in dependencies.items():
            for ref, dt in deps:
                # Check whether we actually know the target of the dependency
                if ref not in mapping:
                    raise parse.ParseError("Found dependency reference to unregistered node.")

                # Add dependency to node dependencies
                node.dependencies.add((mapping[ref], dt))
            del dependencies[node]  # Delete added dependencies to save memory

        # Return root of the tree
        return root

    @staticmethod
    def _parse_clang_node(cursor: clang.Cursor, parent: typing.Optional[ir.IRNode] = None) -> ir.IRNode:
        """
        Parses a Clang AST node identified by a cursor into an IR node.

        :param cursor: The cursor pointing to the node.
        :param parent: The parent IR node.
        :return: The corresponding IR node.
        """
        # Get location
        location = ir.Location(cursor.location.file, cursor.location.line, cursor.location.column)

        # Build node
        node = ir.IRNode(
            typ=cursor.kind.name,
            label=cursor.spelling,
            ref=cursor.get_usr(),
            parent=parent,
            location=location,
            source_obj=cursor,
        )

        return node

    @staticmethod
    def _get_references(cursor: clang.Cursor) -> typing.Generator[clang.Cursor, None, None]:
        """
        Retrieves the reference dependencies from the AST node pointed to by the given cursor.

        :param cursor: The cursor pointing to the node.
        :return: The cursors of the nodes referred to by the node.
        """
        # If the cursor is not a reference, there are no reference dependencies
        if not cursor.kind.is_reference():
            yield from ()

        referenced = cursor.referenced
        declaration = cursor.get_declaration()

        if referenced is not None:
            yield referenced
        if declaration is not None and referenced != declaration:
            yield declaration

    @staticmethod
    def _get_arguments(cursor: clang.Cursor) -> typing.Generator[clang.Cursor, None, None]:
        """
        Retrieves the argument dependencies from the AST node pointed to by the given cursor.

        :param cursor: The cursor pointing to the node.
        :return: The cursors of the nodes of the arguments of the node.
        """
        # If the cursor has arguments, yield them
        yield from cursor.get_arguments()

        # If the cursor is an enum, yield all children
        if cursor.kind == clang.CursorKind.ENUM_DECL:
            for arg_cursor in cursor.walk_preorder():
                yield arg_cursor
