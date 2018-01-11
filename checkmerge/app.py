import sys
import typing

from checkmerge import plugins, version, parse, diff
from checkmerge.diff import gumtree
from checkmerge.ir import tree


def _format_version(*args: typing.Union[int, str]) -> str:
    """Formats a version consisting of multiple segments into a string."""
    if len(args) == 0:
        raise ValueError("Empty versions are not allowed.")

    result = str(args[0])

    # Let separator depend on type of value
    for arg in args[1:]:
        result += '.' if isinstance(arg, int) else '-'
        result += str(arg)

    return result


class CheckMergeMeta(type):
    @property
    def version(cls) -> str:
        """The version number."""
        return _format_version(*version.VERSION)

    @property
    def build(cls) -> str:
        """The build number."""
        return f"{version.BUILD:0>6d}"

    @property
    def platform(cls) -> str:
        """Platform information."""
        return f"Python {_format_version(*sys.version_info)} on {sys.platform}"

    @property
    def plugins(cls) -> typing.Iterable[plugins.Plugin]:
        """The loaded plugins."""
        return plugins.registry.all()

    @property
    def parsers(cls) -> typing.Iterable[parse.Parser]:
        """The loaded parsers."""
        return plugins.registry.parsers.all()

    @property
    def repo(cls) -> str:
        """The URL to the repository."""
        return 'https://github.com/jjkester/checkmerge'

    @property
    def docs(cls) -> str:
        """The URL to the documentation."""
        return cls.repo

    def setup(cls):
        """
        Sets up CheckMerge for use. This method should always be called before CheckMerge is used.

        Among others, the following tasks are executed:
          - Plugins are discovered and loaded from the Python path
          - Available parsers are collected
        """
        plugins.autodiscover()
        plugins.registry.setup()


class CheckMerge(object, metaclass=CheckMergeMeta):
    """
    CheckMerge application instance.
    """
    def __init__(self):
        self._parser: typing.Optional[typing.Type[parse.Parser]] = None

    @property
    def parser(self) -> typing.Optional[typing.Type[parse.Parser]]:
        return self._parser

    @parser.setter
    def parser(self, value: str):
        parser = plugins.registry.parsers.find(value)

        if parser is None:
            raise ValueError(f"No parser with name '{value}' has been found.")

        self._parser = parser

    @property
    def diff_algorithm(self) -> typing.Optional[typing.Type[diff.DiffAlgorithm]]:
        return gumtree.GumTreeDiff

    def parse(self, path: str) -> typing.Optional[tree.IRNode]:
        assert self.parser is not None
        result = self.parser().parse_file(path)
        return result[0] if len(result) > 0 else None

    def diff(self, base: tree.IRNode, other: tree.IRNode) -> diff.DiffResult:
        assert self.diff_algorithm is not None
        assert base is not None and other is not None
        diff_func: diff.DiffAlgorithm = self.diff_algorithm()
        return diff_func(base, other)
