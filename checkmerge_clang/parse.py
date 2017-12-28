import collections
import os
import queue
import tempfile
import typing

import clang.cindex as clang

from checkmerge import parse, ir
from checkmerge_llvm import analysis as llvm


# Customizer type definition
NodeData = typing.Dict[str, typing.Any]
Customizer = typing.Callable[[clang.Cursor, NodeData], NodeData]


class ClangParser(parse.Parser):
    """
    A CheckMerge parser using the Clang compiler.

    As Clang only works with files it is recommended to use parsing from file for efficiency reasons. The other parse
    methods have been implemented to use a temporary file. Therefore, using `parse_stream` with a source file would mean
    a lot of unnecessary IO overhead.
    """
    # Empty list for efficiency purposes
    empty_set: typing.Set[None] = set()

    # Customizers
    _customizers: typing.Dict[clang.CursorKind, Customizer] = dict()

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

        # Get LLVM static analysis results
        analysis_path = llvm.get_analysis_file(path)

        try:
            with open(analysis_path) as analysis_file:
                analysis = llvm.AnalysisParser.parse(analysis_file)
        except FileNotFoundError:
            raise parse.ParseError(f"The analysis file {analysis_path} for {path} does not exist.")
        except IOError:
            raise parse.ParseError(f"Unable to parse analysis file {analysis_path} for {path}."
                                   f"An error occured while reading the file.")

        return [self._walk_ast(tu.cursor, analysis)]

    def _walk_ast(self, cursor: clang.Cursor, analysis: typing.Iterable[llvm.AnalysisNode]) -> ir.IRNode:
        """
        Iterates over the AST to build an IR tree.

        :param cursor: The cursor for the root node of the AST.
        """
        # Lookup table for analysis
        analysis_lookup = collections.defaultdict(set)

        for a in analysis:
            if a.reference and a.reference.location:
                analysis_lookup[a.reference.location].add(a)
            else:
                analysis_lookup[None].add(a)

        # Queue
        walk_queue = queue.LifoQueue()

        # Mapping of declarations (functions, types, ...)
        mapping: typing.Dict[clang.Cursor, ir.IRNode] = {}

        # Temporary dependency storage
        DependencyCache = typing.Dict[ir.IRNode, typing.Set[typing.Tuple[clang.Cursor, ir.DependencyType]]]
        dependencies: DependencyCache = collections.defaultdict(set)

        # Add first element to queue
        walk_queue.put((cursor, None))

        root = None

        # Walk the AST and create the IR tree
        while True:
            try:
                cursor, parent = walk_queue.get_nowait()

                # Build IR node from cursor
                node = self._parse_clang_node(cursor, parent)

                # Set as root if appropriate
                if root is None:
                    root = node

                # Add reference dependencies if appropriate
                dependencies[node].update(((d.canonical.hash, ir.DependencyType.REFERENCE) for d in self._get_references(cursor)))

                # Add arguments of calls and function definitions as dependency
                dependencies[node].update(((d.canonical.hash, ir.DependencyType.ARGUMENT) for d in self._get_arguments(cursor)))

                # Map cursor to node for dependency resolving
                mapping[cursor.canonical.hash] = node

                # Find analysis info
                for analysis_node in analysis_lookup.get(node.location, self.empty_set):
                    # Add to mapping
                    mapping[analysis_node] = node

                    # Add dependencies
                    dependencies[node].update(analysis_node.dependencies)

                # Add children to queue
                for child in cursor.get_children():
                    walk_queue.put_nowait((child, node))
            except queue.Empty:
                # Break out of loop when the queue is empty
                break

        # Resolve dependencies
        for node, deps in dependencies.items():
            for ref, dt in deps:
                rnode = mapping.get(ref, None)

                # Add dependency to node dependencies, ignore if we have no mapping
                if rnode is not None and rnode != node:
                    node.dependencies.add(ir.Dependency(rnode, dt))

        # Return root of the tree
        return root

    @classmethod
    def _parse_clang_node(cls, cursor: clang.Cursor, parent: typing.Optional[ir.IRNode] = None) -> ir.IRNode:
        """
        Parses a Clang AST node identified by a cursor into an IR node.

        :param cursor: The cursor pointing to the node.
        :param parent: The parent IR node.
        :return: The corresponding IR node.
        """
        # Default node data
        kwargs = dict(
            typ=cursor.kind.name,
            label=cursor.spelling,
            ref=cursor.get_usr(),
            parent=parent,
            location=cls._get_location(cursor),
            source_obj=cursor,
        )

        # Overrides for specific kinds of nodes
        if cursor.kind in cls._customizers:
            cls._customizers[cursor.kind](cursor, kwargs)

        # Build node
        node = ir.IRNode(**kwargs)

        return node

    @classmethod
    def register_customizer(cls, *kinds: clang.CursorKind) -> typing.Callable[[Customizer], Customizer]:
        """
        Decorator for registering customizations for the creation of IR nodes from Clang AST cursors.

        :param kinds: The Clang cursor kinds to use the customization for.
        :return: The decorator for the customization function.
        """
        def decorator(func):
            for kind in kinds:
                if kind in cls._customizers:
                    raise ValueError(f"Cannot add {func} as customizer for {kind}, another customizer was already"
                                     f"registered.")
                cls._customizers[kind] = func
            return func
        return decorator

    @staticmethod
    def _get_location(obj: typing.Union[clang.Cursor, clang.Token]) -> ir.Location:
        """
        Returns the location as IR location from a Clang object with a location associated with it.
        """
        location: clang.SourceLocation = obj.location
        file: typing.Optional[clang.File] = location.file

        if file is None:
            cursor = obj if isinstance(obj, clang.Cursor) else obj.cursor
            filename = cursor.translation_unit.spelling
        else:
            filename = file.name

        return ir.Location(file=filename, line=location.line, column=location.column)

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
        declaration = cursor.get_definition()

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


@ClangParser.register_customizer(clang.CursorKind.TYPEDEF_DECL)
def customize_typedef_decl(cursor: clang.Cursor, kwargs: NodeData) -> NodeData:
    """Sets the label of a typedef to its underlying type."""
    try:
        kwargs['label'] = cursor.underlying_typedef_type.spelling
    except AttributeError:
        raise parse.ParseError("Unexpected error: typedef does not have an underlying type.")
    return kwargs


clang_literals = [
    clang.CursorKind.INTEGER_LITERAL,
    clang.CursorKind.FLOATING_LITERAL,
    clang.CursorKind.IMAGINARY_LITERAL,
    clang.CursorKind.STRING_LITERAL,
    clang.CursorKind.CHARACTER_LITERAL,
]


@ClangParser.register_customizer(*clang_literals)
def customize_literals(cursor: clang.Cursor, kwargs: NodeData) -> NodeData:
    """Sets the label to the token value of the literal."""
    try:
        kwargs['label'] = ''.join(map(lambda x: x.spelling, cursor.get_tokens()))
    except AttributeError:
        raise parse.ParseError("Unexpected error: literal does not have any tokens.")
    return kwargs


clang_operators = [
    clang.CursorKind.UNARY_OPERATOR,
    clang.CursorKind.BINARY_OPERATOR,
    clang.CursorKind.COMPOUND_ASSIGNMENT_OPERATOR,
    clang.CursorKind.CONDITIONAL_OPERATOR,
]


@ClangParser.register_customizer(*clang_operators)
def customize_operator(cursor: clang.Cursor, kwargs: NodeData) -> NodeData:
    """Sets the label and location to that of the actual operator token."""
    tokens = {f"{t.location.line}:{t.location.column}:{t.spelling}": t for t in cursor.get_tokens()}

    # Find token not in any of the child ranges - that should be the operator
    for child in cursor.get_children():
        for t in child.get_tokens():
            string = f"{t.location.line}:{t.location.column}:{t.spelling}"
            if string in tokens:
                del tokens[string]

    if len(tokens) < 1:
        raise parse.ParseError("Unexpected error: operator does not have any non-child tokens.")

    tokens = list(map(lambda y: y[1], sorted(tokens.items(), key=lambda x: x[0])))

    if len(tokens) > 0:
        kwargs['location'] = ClangParser._get_location(tokens[0])

    kwargs['label'] = ''.join(map(lambda x: x.spelling, tokens))
    print(kwargs['parent'], kwargs['typ'], kwargs['label'], kwargs['location'].line, kwargs['location'].column)
    return kwargs
