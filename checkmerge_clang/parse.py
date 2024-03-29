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
    key = 'clang'
    name = 'Clang'
    description = 'Parser using the Clang compiler. See documentation for specific requirements.'

    # Empty list for efficiency purposes
    empty_set: typing.Set[None] = set()

    # Customizers
    _customizers: typing.Dict[clang.CursorKind, Customizer] = dict()

    # Clang args
    _clang_args = []

    def parse_str(self, val: str) -> typing.List[ir.Node]:
        # Create temporary file to work with
        with tempfile.NamedTemporaryFile() as f:
            # Write string to file
            f.write(val)

            # Parse from file
            return self.parse_file(f.name)

    def parse_stream(self, stream: typing.IO) -> typing.List[ir.Node]:
        # Create temporary file to work with
        with tempfile.NamedTemporaryFile() as f:
            # Write string to file
            f.write(stream.read())

            # Parse from file
            return self.parse_file(f.name)

    def parse_file(self, path: str) -> typing.List[ir.Node]:
        # Create index for parsing
        index = clang.Index.create()

        # Check if file exists
        if not os.path.isfile(path):
            raise parse.ParseError(f"The file {path} does not exist.")

        # Try if parsing the code is successful
        try:
            tu = index.parse(path=path, args=self._clang_args)
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

        return [self.walk_ast(tu.cursor, analysis)]

    def walk_ast(self, cursor: clang.Cursor, analysis: typing.Iterable[llvm.AnalysisNode]) -> ir.Node:
        """
        Iterates over the AST to build an IR tree. The provided analysis nodes are matched to nodes from the AST and the
        analysis results encoded in the analysis nodes is added to the IR tree.

        :param cursor: The cursor for the root node of the AST.
        :param analysis: The LLVM analysis results.
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
        mapping: typing.Dict[clang.Cursor, ir.Node] = {}

        # Temporary dependency storage
        DependencyCache = typing.Dict[ir.Node, typing.Set[typing.Tuple[clang.Cursor, ir.DependencyType]]]
        dependencies: DependencyCache = collections.defaultdict(set)

        # Add first element to queue
        walk_queue.put((cursor, None))

        root = None

        # Walk the AST and create the IR tree
        while True:
            try:
                cursor, parent = walk_queue.get_nowait()

                # Build IR node from cursor
                node = self.parse_clang_node(cursor, parent)

                # Set as root if appropriate
                if root is None:
                    root = node

                # Add reference dependencies if appropriate
                dependencies[node].update(((d.canonical.hash, ir.DependencyType.REFERENCE)
                                           for d in self.get_references(cursor)))

                # Add arguments of calls and function definitions as dependency
                dependencies[node].update(((d.canonical.hash, ir.DependencyType.ARGUMENT)
                                           for d in self.get_arguments(cursor)))

                # Map cursor to node for dependency resolving
                mapping[cursor.canonical.hash] = node

                alt_location = ir.Location(node.location.file, node.location.line, node.location.column + node.label.find(': ') + 1)
                analysis_nodes = analysis_lookup.get(node.location, self.empty_set).copy()

                for analysis_node in analysis_lookup.get(alt_location, self.empty_set):
                    analysis_nodes.add(analysis_node)

                # Find analysis info
                for analysis_node in analysis_nodes:
                    # Map analysis node to IR node for resolving references
                    mapping[analysis_node] = node

                    # Add dependencies
                    dependencies[node].update(analysis_node.dependencies)

                # Add children to queue
                for child in reversed(list(cursor.get_children())):
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
                    node.add_dependencies(ir.Dependency(rnode, dt))

        # Return root of the tree
        return root

    @classmethod
    def parse_clang_node(cls, cursor: clang.Cursor, parent: typing.Optional[ir.Node] = None) -> ir.Node:
        """
        Parses a Clang AST node identified by a cursor into an IR node.

        :param cursor: The cursor pointing to the node.
        :param parent: The parent IR node.
        :return: The corresponding IR node.
        """
        type_str = getattr(cursor.type, 'spelling', '')

        # Build label
        label = f"{type_str}: {cursor.spelling}" if cursor.is_definition() and type_str else cursor.spelling

        # Default node data
        kwargs = dict(
            typ=cursor.kind.name,
            label=label,
            ref=cursor.get_usr(),
            parent=parent,
            source_range=cls.get_range(cursor),
        )

        # Overrides for root node
        if parent is None and cursor.kind == clang.CursorKind.TRANSLATION_UNIT:
            kwargs['label'] = os.path.basename(kwargs['label'])

        # Overrides for specific kinds of nodes
        if cursor.kind in cls._customizers:
            cls._customizers[cursor.kind](cursor, kwargs)

        # Build node
        node = ir.Node(**kwargs)

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
    def get_location(obj: typing.Union[clang.Cursor, clang.Token]) -> ir.Location:
        """
        Returns the location as IR location from a Clang object with a location associated with it.
        """
        location: clang.SourceLocation = obj.location
        return ClangParser._transform_location(location)

    @staticmethod
    def get_range(obj: typing.Union[clang.Cursor, clang.Token]) -> ir.Range:
        """
        Returns the location range as IR location range from a Clang object with a location associated with it.
        """
        extent: clang.SourceRange = obj.extent
        return ir.Range(start=ClangParser._transform_location(extent.start), end=ClangParser._transform_location(extent.end))

    @staticmethod
    def _transform_location(location: clang.SourceLocation) -> ir.Location:
        file: typing.Optional[clang.File] = location.file
        filename = file.name if file is not None else ''
        return ir.Location(file=filename, line=location.line, column=location.column)

    @staticmethod
    def get_references(cursor: clang.Cursor) -> typing.Generator[clang.Cursor, None, None]:
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
    def get_arguments(cursor: clang.Cursor) -> typing.Generator[clang.Cursor, None, None]:
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
    """
    Sets the label of a typedef to its underlying type. Without this customization the label would be the name of the
    typedef which is not representative of possible changes to the typedef.
    """
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
    """
    Sets the label to the token value of the literal. Without this customization a literal would not have a label at
    all.
    """
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
    """
    Sets the label and location to that of the actual operator token. Without this customization an operator would not
    have a label. The libclang library does not expose the proper function for this.
    """
    # Get all tokens
    tokens = {f"{t.location.line}:{t.location.column}:{t.spelling}": t for t in cursor.get_tokens()}

    # Remove tokens of children to be left with the actual operator token(s)
    for child in cursor.get_children():
        for key in (f"{t.location.line}:{t.location.column}:{t.spelling}" for t in child.get_tokens()):
            tokens.pop(key, None)

    # if len(tokens) < 1:
    #     raise parse.ParseError("Unexpected error: Operator does not have any non-child tokens.")

    # Get token objects ordered properly
    tokens = list(map(lambda y: y[1], sorted(tokens.items(), key=lambda x: x[0])))

    # if len(tokens) > 0:
    #     kwargs['source_range'] = ir.Range(ClangParser.get_location(tokens[0]), ClangParser.get_location(tokens[-1]))

    kwargs['label'] = ''.join(map(lambda x: x.spelling, tokens))
    return kwargs


@ClangParser.register_customizer(clang.CursorKind.RETURN_STMT)
def customize_return(cursor: clang.Cursor, kwargs: NodeData) -> NodeData:
    """
    Sets the `is_memory_operation` flag for returns.
    """
    kwargs['is_memory_operation'] = True
    return kwargs
