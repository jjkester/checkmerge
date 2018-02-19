import sys
import typing
from contextlib import contextmanager
from copy import copy

from checkmerge import analysis as _analysis, diff as _diff, ir, parse, plugins, version
from checkmerge.diff import gumtree


# Type variables
T = typing.TypeVar('T')


def format_version(*args: typing.Union[int, str]) -> str:
    """
    Formats a version consisting of multiple segments into a string.

    If a segment is an integer, it will be separated from the preceding segment with a dot. If a segment is a string,
    it will be separated with a dash.

    :param args: The segments representing the version.
    :return: The string representation of the version.
    """
    if len(args) == 0:
        raise ValueError("Empty versions are not allowed.")

    result = str(args[0])

    # Let separator depend on type of value
    for arg in args[1:]:
        result += '.' if isinstance(arg, int) else '-'
        result += str(arg)

    return result


class CheckMergeMeta(type):
    """
    Metaclass for the CheckMerge object containing information that should be globally accessible.
    """
    _initialized = False

    @property
    def version(cls) -> str:
        """The version number of the installed CheckMerge version."""
        return format_version(*version.VERSION)

    @property
    def build(cls) -> str:
        """The build number of the installed CheckMerge version."""
        return f"{version.BUILD:0>6d}"

    @property
    def platform(cls) -> str:
        """Platform specifics of the current runtime."""
        return f"Python {format_version(*sys.version_info)} on {sys.platform}"

    @property
    def plugins(cls) -> typing.Iterable[plugins.Plugin]:
        """The loaded plugins."""
        return plugins.registry.all()

    @property
    def parsers(cls) -> typing.Iterable[typing.Type[parse.Parser]]:
        """The loaded parsers."""
        return plugins.registry.parsers.all()

    @property
    def analysis(cls) -> typing.Iterable[typing.Type[_analysis.Analysis]]:
        """The loaded analysis."""
        return plugins.registry.analysis.all()

    @property
    def repo(cls) -> str:
        """The URL to the main repository."""
        return 'https://github.com/jjkester/checkmerge'

    @property
    def docs(cls) -> str:
        """The URL to the documentation."""
        return cls.repo

    @property
    def ready(cls) -> bool:
        """Whether CheckMerge is ready for use. Run `setup()` to initialize CheckMerge."""
        return cls._initialized

    def setup(cls):
        """
        Sets up CheckMerge for use. This method should always be called before CheckMerge is used.

        Among others, the following tasks are executed:
          - Plugins are discovered and loaded from the Python path
          - Available parsers are collected
        """
        # Quit if already initialized
        if cls._initialized:
            return

        plugins.autodiscover()
        plugins.registry.setup()

        # Mark as initialized
        cls._initialized = True


class CheckMerge(object, metaclass=CheckMergeMeta):
    """
    CheckMerge application instance.
    """

    def __init__(self):
        self._parser: typing.Optional[typing.Type[parse.Parser]] = None
        self._options: typing.Dict[str, typing.Any] = {}

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
    def diff_algorithm(self) -> typing.Optional[typing.Type[_diff.DiffAlgorithm]]:
        return gumtree.GumTreeDiff

    @property
    def options(self) -> typing.Dict[str, typing.Any]:
        return copy(self._options)

    def set_options(self, **kwargs) -> None:
        self._options.update(**kwargs)

    def build_config(self) -> "RunConfig":
        """
        Builds and returns a run configuration from the settings in this app.
        """
        return RunConfig(
            parse_cls=self.parser,
            diff_cls=self.diff_algorithm,
            **self.options,
        )


class RunConfig(object):
    """
    A run configuration. When configured using the correct classes this object can be used to declaratively define the
    analysis that should be carried out.
    """

    def __init__(self, parse_cls: typing.Type[parse.Parser], diff_cls: typing.Type[_diff.DiffAlgorithm], **options):
        # Set initial fields
        self.parser = parse_cls
        self.differ = diff_cls
        self.options = options

        # Initialize data fields
        self._base_path: str = None
        self._other_path: str = None
        self._ancestor_path: str = None
        self._base_tree: ir.Node = None
        self._other_tree: ir.Node = None
        self._ancestor_tree: ir.Node = None
        self._diff_result: _diff.DiffResult = None
        self._analysis_chain: typing.List[typing.Tuple[_analysis.Analysis, typing.Tuple]] = []

    def parse(self, base_path: str, other_path: str, ancestor_path: typing.Optional[str] = None) -> "RunConfig":
        """
        Parses two programs into internal representation trees.

        :param base_path: The path to the base program to parse.
        :param other_path: The path to the other program to parse.
        :param ancestor_path: (Optional) The path to the ancestor of both programs to parse.
        """
        # Copy instance
        rc = copy(self)

        # Construct parser
        parser = rc.parser()

        # Parse trees
        with rc._arg(base_path, '_base_path') as base_path, rc._arg(other_path, '_other_path') as other_path,\
                rc._arg(ancestor_path, '_ancestor_path') as ancestor_path:
            base_tree = parser.parse_file(base_path)[0]
            other_tree = parser.parse_file(other_path)[0]
            ancestor_tree = parser.parse_file(ancestor_path)[0] if ancestor_path is not None else None

        # Store results
        rc._base_tree, rc._other_tree, rc._ancestor_tree = base_tree, other_tree, ancestor_tree

        return rc

    def diff(self, base: typing.Optional[ir.Node] = None, other: typing.Optional[ir.Node] = None,
             ancestor: typing.Optional[ir.Node] = None) -> "RunConfig":
        """
        Calculates the difference between two internal representation trees.

        :param base: The base tree.
        :param other: The other tree.
        :param ancestor: The common ancestor tree.
        """
        # Copy instance
        rc = copy(self)

        # Construct differ
        differ = rc.differ()

        # Diff trees
        with rc._arg(base, '_base_tree') as base, rc._arg(other, '_other_tree') as other,\
                rc._arg(ancestor, '_ancestor_tree') as ancestor:
            if ancestor is not None:
                # Diff each version since the common ancestor
                base_result = differ(ancestor, base)
                other_result = differ(ancestor, other)

                # Merge results to get the matching nodes between the two versions
                mapping = _diff.combine_mappings(base_result.mapping, other_result.mapping)

                # Try to remove matching changes by diffing the two versions, assuming the mappings from the ancestor
                two_way_result = differ(base, other, mapping)

                # Build a combined result
                result = _diff.MergeDiffResult(base, other, ancestor, base_result, other_result, two_way_result)
            else:
                # Diff the two versions
                result = differ(base, other)

        # Tag nodes with changes
        _diff.tag_nodes(result)

        # Store results
        rc._diff_result = result

        return rc

    def analyze(self, analysis_cls: typing.Type[_analysis.Analysis],
                changes: typing.Optional[_diff.DiffResult] = None) -> "RunConfig":
        """
        Schedules the provided analysis. Evaluation is lazy.

        :param analysis_cls: The analysis class to use.
        :param changes: The diff result.
        """
        # Copy instance
        rc = copy(self)

        # Construct analyzer
        analysis = analysis_cls()

        # Store analysis generator
        with rc._arg(changes, '_diff_result') as changes:
            rc._analysis_chain.append((analysis, (changes,)))

        return rc

    def trees(self) -> typing.Tuple[ir.Node, ir.Node]:
        """
        Returns the parsed trees.
        """
        if self._base_tree is None or self._other_tree is None:
            raise ValueError("There are no parsed trees, run parse() first.")
        return self._base_tree, self._other_tree

    def changes(self) -> _diff.DiffResult:
        """
        Returns the changes between the trees.
        """
        if self._diff_result is None:
            raise ValueError("There is no diff result, run diff() first.")
        return self._diff_result

    def analysis(self) -> _analysis.AnalysisResultGenerator:
        """
        Returns a generator yielding the analysis results.
        """
        for func, args in self._analysis_chain:
            yield from func(*args)

    @contextmanager
    def _arg(self, value: T, key: str) -> T:
        if value is None:
            value = getattr(self, key, None)
        yield value
        setattr(self, key, value)

    @contextmanager
    def _args(self, *args: typing.Tuple[T, str]) -> T:
        values = tuple((getattr(self, k) if v is None else v for v, k in args))
        yield values
        for k, v in zip((k for v, k in args), values):
            setattr(self, k, v)
