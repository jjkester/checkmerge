import sys
import typing

from checkmerge import plugins, version, parse


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
