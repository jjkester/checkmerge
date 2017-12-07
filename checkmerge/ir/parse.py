import typing

import yaml

from checkmerge.ir import types as ir

# Define stream type
Stream = typing.Union[typing.AnyStr, typing.IO]


class IRParser(object):
    """
    Parses the analysis IR from text representation to Python objects.
    """
    def __init__(self):
        # Initialize data structures
        self._modules = {}  # type: typing.Dict[str, ir.Module]
        self._module = None  # type: typing.Optional[ir.Module]
        self._function = None  # type: typing.Optional[ir.Function]
        self._block = None  # type: typing.Optional[ir.Block]
        self._instruction = None  # type: typing.Optional[ir.Instruction]
        self._dependency_refs = {}  # type: typing.Dict[str, ir.IRNode]
        self._dependencies = {}  # type: typing.Dict[ir.Instruction, typing.List[str]]

        # Initialize YAML implementation
        self._Loader = None
        self._init_yaml()

    @classmethod
    def parse(cls, stream: Stream) -> typing.List[ir.Module]:
        """
        Parses the text representation of the CheckMerge analysis IR into the appropriate Python data structures.

        :param stream: A string or file-like object containing the data.
        :return: List of the parsed root nodes.
        """
        parser = cls()
        return parser._parse(stream)

    def _parse(self, stream: Stream) -> typing.List[ir.Module]:
        # Get pure Python
        raw = self._read(stream)

        # Check data structures
        assert isinstance(raw, dict)

        # Visit functions
        for function in raw.items():
            self._function = self._visit_function(*function)


        return list(self._modules.values())

    def _get_module(self, name) -> ir.Module:
        # Check data structure
        assert isinstance(name, str)

        # Register module if needed
        if name not in self._modules:
            self._modules[name] = ir.Module(
                uid=name,
                name=name,
            )

        return self._modules[name]

    def _visit_function(self, name, data) -> ir.Function:
        # Check data structure
        assert isinstance(name, str)
        assert isinstance(data, dict)
        assert 'name' in data
        assert 'module' in data
        assert 'location' in data

        # Clear out old dependency information
        self._dependency_refs.clear()
        self._dependencies.clear()

        # Visit module
        module = self._get_module(data['module'])

        # Create function
        self._function = ir.Function(
            uid=name,
            name=data['name'],
            module=module,
            location=ir.Location.parse(data['location'])
        )

        # Filter out blocks
        blocks = {k: v for k, v in data.items() if isinstance(k, str) and k.startswith('block.')}

        # Visit children
        for block in blocks.items():
            self._visit_block(*block)

        # Resolve dependencies
        self._resolve_dependencies(self._dependencies, self._dependency_refs)

        return self._function

    def _visit_block(self, name, data):
        # Check data structure
        assert isinstance(name, str)
        assert isinstance(data, list)

        # Create block
        self._block = ir.Block(
            uid=name,
            name=name,
            function=self._function
        )

        # Set dependency ref
        self._dependency_refs[name] = self._block

        # Visit children
        for item in data:
            assert isinstance(item, dict)
            assert len(item) == 1

            self._visit_instruction(*list(item.items())[0])

        return self._block

    def _visit_instruction(self, name, data):
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
            location = self._function.location.file + location

        # Create instruction
        self._instruction = ir.Instruction(
            uid=name,
            block=self._block,
            opcode=data.get('opcode'),
            variable=variable,
            location=location
        )

        # Set dependency ref
        self._dependency_refs[name] = self._instruction

        # Set dependencies
        if 'dependencies' in data:
            dependencies = data['dependencies']

            assert isinstance(dependencies, list)

            self._dependencies[self._instruction] = [d[1:] for d in dependencies if isinstance(d, str) and d.startswith('*')]

        return self._instruction

    @staticmethod
    def _resolve_dependencies(data: typing.Dict[ir.Instruction, typing.List[str]], lookup: typing.Dict[str, ir.IRNode]):
        for instruction, dependencies in data.items():
            for dependency in dependencies:
                foreign_obj = lookup.get(dependency)

                if foreign_obj:
                    assert isinstance(foreign_obj, (ir.Instruction, ir.Block))
                    instruction.register_dependency(foreign_obj)
                else:
                    raise ValueError(f"Invalid dependency {dependency} for instruction {instruction.key} in function {self._function.key}.")

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
