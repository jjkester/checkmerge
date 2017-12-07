import collections
import typing


# Type variables to improve static typing
T = typing.TypeVar('T')
K = typing.TypeVar('K')


class Location(object):
    """
    Location in source code.
    """
    def __init__(self, file: str, line: int, column: int):
        """
        :param file: The file name or path. May be the empty string if unknown.
        :param line: The line number in the file.
        :param column: The column number in the line.
        """
        # Set properties
        self.file = file  # type: str
        self.line = line  # type: int
        self.column = column  # type: int

    def __str__(self):
        return f"{self.file}:{self.line}:{self.column}"

    def __eq__(self, other):
        if not isinstance(other, Location):
            return super(Location, self).__eq__(other)

        # Test lines and columns
        eq = self.line == other.line and self.column == other.column

        # Test files if present
        if self.file and other.file:
            eq = eq and self.file == other.file

        return eq

    def __ne__(self, other):
        return not self.__eq__(other)

    @classmethod
    def parse(cls: typing.Type["Location"], value: str) -> "Location":
        """
        Parses a semicolon `:` separated location string in the format `filename:line:column`.

        :param value: The location string.
        :return: A new instance.
        """
        segments = value.split(':')

        if len(segments) != 3:
            raise ValueError(f"The location string {value} is invalid.")

        return cls(*segments)


class IRNode(object):
    """
    Base class for nodes of the internal representation tree.
    """
    def __init__(self, uid: str, location: typing.Optional[Location] = None):
        # Set properties
        self.uid = uid  # type: str
        self._location = location  # type: Location

    def __str__(self):
        return self.key

    def register_child(self, obj: object):
        """
        Register the given object as child of this node. May raise a `TypeError` if the object is of the incorrect type
        and a `ValueError` if for some reason it is not allowed to register the given object.

        :param obj: The object to register.
        """
        raise TypeError(f"Object of type {type(obj)} cannot be registered, no appropriate registry available.")

    @staticmethod
    def _register(cls: typing.Type[T], obj: T, key: K, registry: typing.Dict[K, T]):
        """
        Internal function to register children of a node. Contains repeating logic for checking the type and uniqueness
        of registered objects.

        :param cls: The expected type of the object.
        :param obj: The object to register.
        :param key: The key of the object to register.
        :param registry: The registry to register the object in.
        """
        # Type checking
        if not isinstance(obj, cls):
            raise TypeError(f"Object of type {type(obj)} cannot be registered, expected object of type {cls}.")

        # Uniqueness checking
        if key in registry and obj != registry[key]:
            raise ValueError(f"Duplicate object {obj} cannot be registered.")

        # Actually register
        registry[key] = obj

    @property
    def key(self):
        return self.uid

    @property
    def location(self):
        return self._location


class Module(IRNode):
    """
    A module encloses functions in a program.
    """
    def __init__(self, uid: str, name: str, *args, **kwargs):
        super(Module, self).__init__(uid, *args, **kwargs)

        # Set properties
        self.name = name  # type: str

        # Initialize data structures
        self.functions = collections.OrderedDict()  # type: typing.Dict[str, Function]

    def register_child(self, obj: "Function"):
        """
        Register a function to be part of this module.

        :param obj: The function to register.
        """
        self._register(Function, obj, obj.key, self.functions)

    @property
    def key(self):
        return self.name


class Function(IRNode):
    """
    A function in a program.
    """
    def __init__(self, uid: str, name: str, module: typing.Optional[Module] = None, *args, **kwargs):
        super(Function, self).__init__(uid, *args, **kwargs)

        # Set properties
        self.name = name  # type: str
        self.module = module  # type: typing.Optional[Module]

        # Initialize data structures
        self.blocks = collections.OrderedDict()  # type: typing.Dict[str, Block]

        # Register function
        if module:
            module.register_child(self)

    def register_child(self, obj: "Block"):
        """
        Register a block to be part of this function.

        :param obj: The block to register.
        """
        self._register(Block, obj, obj.key, self.blocks)


class Block(IRNode):
    """
    A block containing instructions.
    """
    def __init__(self, uid: str, name: str, function: Function, *args, **kwargs):
        super(Block, self).__init__(uid, *args, **kwargs)

        # Set properties
        self.name = name  # type: str
        self.function = function  # type: Function

        # Initialize data structures
        self.instructions = collections.OrderedDict()  # type: typing.Dict[str, Instruction]

        # Register block
        function.register_child(self)

    def register_child(self, obj: "Instruction"):
        """
        Register an instruction to be part of this block.

        :param obj: The instruction to register.
        """
        self._register(Instruction, obj, obj.key, self.instructions)

    @property
    def key(self):
        return self.name


class Instruction(IRNode):
    """
    An instruction in a program.
    """
    def __init__(self, uid: str, block: Block, opcode: typing.Optional[str] = None, variable: typing.Optional[str] = None, *args, **kwargs):
        super(Instruction, self).__init__(uid, *args, **kwargs)

        # Set properties
        self.block = block  # type: Block
        self.opcode = opcode  # type: typing.Optional[str]
        self.variable = variable  # type: typing.Optional[str]

        # Initialize data structures
        self.dependencies = []  # type: typing.List[typing.Union[Instruction, Block]]

        # Register instruction
        block.register_child(self)

    def register_dependency(self, obj: typing.Union["Instruction", Block]):
        """
        Registers an instruction or block as dependency of this instruction.

        :param obj: The dependency to register.
        """
        if not isinstance(obj, (Instruction, Block)):
            raise TypeError("Only instructions and blocks are valid dependencies.")

        if obj == self:
            raise ValueError("An instruction cannot be a dependency of itself.")

        if obj not in self.dependencies:
            self.dependencies.append(obj)
