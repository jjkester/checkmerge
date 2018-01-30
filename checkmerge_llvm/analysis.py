import collections
import typing

import yaml

from checkmerge import ir
from checkmerge_llvm.checkmerge_llvm import get_analysis_file


# Define stream type
Stream = typing.Union[typing.AnyStr, typing.IO]


class SourceReference(object):
    """
    Reference to a source code object.
    """
    __slots__ = ('location', 'entity_name')

    def __init__(self, location: ir.Location, entity_name: typing.Optional[str] = None):
        self.location = location
        self.entity_name = entity_name

    def __eq__(self, other):
        if isinstance(other, SourceReference):
            eq = self.location == other.location
            if self.entity_name is not None or other.entity_name is not None:
                eq = self.entity_name == other.entity_name
            return eq
        return super().__eq__(other)


class AnalysisNode(object):
    """
    Container for LLVM static analysis data.
    """
    __slots__ = ('reference', 'dependencies')

    def __init__(self, reference: SourceReference):
        self.reference = reference
        self.dependencies: typing.Set[typing.Tuple[AnalysisNode, ir.DependencyType]] = set()


class AnalysisParser(object):
    """
    Parses the LLVM analysis information generated by CheckMerge-LLVM into Python objects.
    """
    def __init__(self):
        # Initialize data structures
        self._dependency_refs: typing.Dict[str, AnalysisNode] = {}
        self._dependencies: typing.Dict[AnalysisNode, typing.Set[typing.Tuple[str, str]]] = collections.defaultdict(set)

        # Initialize YAML implementation
        self._Loader = None
        self._init_yaml()

    @classmethod
    def parse(cls, stream: Stream) -> typing.Set[AnalysisNode]:
        """
        Parses the LLVM analysis information into the appropriate Python data structures.

        :param stream: A string or file-like object containing the data.
        :return: List of the parsed root nodes.
        """
        parser = cls()
        return set(parser._parse(stream))

    def _parse(self, stream: Stream) -> typing.Generator[AnalysisNode, None, None]:
        # Get pure Python
        raw = self._read(stream)

        # Check data structures
        assert isinstance(raw, dict)

        # Visit functions
        for function in raw.items():
            yield from self._visit_function(*function)

    def _visit_function(self, name, data) -> typing.Generator[AnalysisNode, None, None]:
        # Check data structure
        assert isinstance(name, str)
        assert isinstance(data, dict)
        assert 'name' in data
        assert 'module' in data
        assert 'location' in data

        # Clear out old dependency information
        self._dependency_refs.clear()
        self._dependencies.clear()

        # Create function node
        self._function = AnalysisNode(SourceReference(
            location=ir.Location.parse(data['location']),
            entity_name=data['name']
        ))

        # Filter out blocks
        blocks = {k: v for k, v in data.items() if isinstance(k, str) and k.startswith('block.')}

        # Visit children
        for block in blocks.items():
            yield from self._visit_block(*block)

        # Resolve dependencies
        self._resolve_dependencies()

        yield self._function

    def _visit_block(self, name, data) -> typing.Generator[AnalysisNode, None, None]:
        # Check data structure
        assert isinstance(name, str)
        assert isinstance(data, list)

        # Visit children
        for item in data:
            assert isinstance(item, dict)
            assert len(item) == 1

            yield from self._visit_instruction(*list(item.items())[0])

    def _visit_instruction(self, name, data) -> typing.Generator[AnalysisNode, None, None]:
        # Check data structure
        assert isinstance(name, str)
        assert isinstance(data, dict)

        # Preprocessing
        location = data.get('location')  # type: typing.Optional[str]

        if 'variable' in data:
            assert isinstance(data['variable'], dict)

        variable = data.get('variable')

        if not location and variable:
            location = variable.get('location')

        if location and location.startswith(':'):
            location = self._function.reference.location.file + location

        # Create instruction
        self._instruction = AnalysisNode(SourceReference(
            entity_name=variable.get('name') if variable else None,
            location=ir.Location.parse(location)
        ))

        # Set dependency ref
        self._dependency_refs[name] = self._instruction

        # Set dependencies
        if 'dependencies' in data and data['dependencies'] is not None:
            dependencies = data['dependencies']

            assert isinstance(dependencies, dict)

            self._dependencies[self._instruction].update(((d[1:], t) for d, t in dependencies.items() if isinstance(d, str) and d.startswith('*')))

        yield self._instruction

    def _resolve_dependencies(self):
        data = self._dependencies
        lookup = self._dependency_refs

        for dependant, dependencies in data.items():
            for ref, typ in dependencies:
                dependency = lookup.get(ref)
                dependency_type = ir.DependencyType.OTHER

                if typ == "RAW":
                    dependency_type = ir.DependencyType.FLOW
                elif typ == "WAR":
                    dependency_type = ir.DependencyType.ANTI
                elif typ == "WAW":
                    dependency_type = ir.DependencyType.OUTPUT
                elif typ == "RAR":
                    dependency_type = ir.DependencyType.INPUT
                elif typ == "RAU":
                    dependency_type = ir.DependencyType.FLOW
                elif typ == "WAU":
                    dependency_type = ir.DependencyType.ANTI

                if dependency:
                    assert isinstance(dependency, AnalysisNode)
                    dependant.dependencies.add((dependency, dependency_type))

    def _init_yaml(self):
        """
        Initializes the YAML parser. Chooses to use the LibYAML C implementation when available.
        """
        native = hasattr(yaml, 'CLoader')
        self._Loader = yaml.CLoader if native else yaml.Loader

    def _read(self, stream: Stream):
        """
        Parses the input data and returns its pure Python representation.

        :param stream: The input data as string or file-like object.
        :return: The pure Python representation of the data.
        """
        if not self._Loader:
            raise AssertionError("The YAML loader has not been correctly initialized.")
        return yaml.load(stream, Loader=self._Loader)


__all__ = [
    SourceReference,
    AnalysisNode,
    AnalysisParser,
    get_analysis_file,
]
