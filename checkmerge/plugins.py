import importlib
import os
import sys
import typing

from checkmerge import analysis, parse
from checkmerge.util.registry import Registry


class KeyRegistry(Registry):
    """
    Registry for classes with a `key` class parameter.
    """

    def key(self, cls):
        return cls.key


class PluginRegistry(KeyRegistry):
    """
    Manages the available CheckMerge plugins.
    """

    def __init__(self):
        super(PluginRegistry, self).__init__()
        self.parsers: Registry[str, parse.Parser] = KeyRegistry()
        self.analysis: Registry[str, analysis.Analysis] = KeyRegistry()

    def register(self, cls):
        # Register instance instead of class
        return super().register(cls())

    def setup(self):
        """
        Sets up the registered plugins. Marks plugins with errors as disabled. Registers functionality from the plugins
        in the appropriate sub registers.
        """
        for plugin in self.registry.values():
            # Skip plugin if it is already loaded
            if plugin.ready:
                continue

            # Try to setup plugin, disable if an error occurs
            try:
                plugin.setup()
            except Exception as e:
                plugin.disable(reason=str(e))

            # Pull functions from plugin
            if plugin.ready:
                for cls in plugin.provide_parsers():
                    assert issubclass(cls, parse.Parser)
                    self.parsers.register(cls)
                for cls in plugin.provide_analysis():
                    assert issubclass(cls, analysis.Analysis)
                    self.analysis.register(cls)

    def _filter(self, item: "Plugin") -> bool:
        return not item.disabled


# Define the global plugin registry
registry = PluginRegistry()


def autodiscover() -> None:
    """
    Tries to automatically discover defined plugins by loading the `plugin` module of each package on the python path.
    """
    search_directories: typing.List[str] = list()

    # Add nested packages
    search_directories.append(os.path.dirname(os.path.dirname(__file__)))

    # Add packages from pythonpath
    search_directories.extend(sys.path)

    for d in filter(lambda x: os.path.isdir(x), search_directories):
        for p in os.listdir(d):
            if os.path.isfile(os.path.join(d, p, 'plugin.py')):
                importlib.import_module(f'{os.path.basename(p)}.plugin')


class PluginBase(type):
    """
    Metaclass for CheckMerge plugin definitions.
    """

    def __new__(mcs, name, bases, attrs):
        cls = super(PluginBase, mcs).__new__(mcs, name, bases, attrs)

        if cls.__module__ is not mcs.__module__:
            registry.register(cls)

        return cls


class Plugin(object, metaclass=PluginBase):
    """
    Base class for CheckMerge plugin definitions.

    Plugin objects are automatically registered, provided the module in which they are located is imported.
    """
    key: str = ''  # Identifier of the plugin
    name: str = ''  # Human-readable name of the plugin
    description: str = ''  # Human-readable description of the plugin

    def __init__(self):
        self._initialized: bool = False
        self._disabled: bool = False
        self._disable_reason: str = ''

    def provide_parsers(self) -> typing.List[typing.Type[parse.Parser]]:
        """
        Returns a list of the parsers provided by this plugin.

        :return: The parsers provided by this plugin.
        """
        return []

    def provide_analysis(self) -> typing.List[typing.Type[analysis.Analysis]]:
        """
        Returns a list of the analysis classes provided by this plugin.

        :return: The analysis classes provided by this plugin.
        """
        return []

    def setup(self):
        """
        Performs plugin initialization before it is used.
        """
        self._initialized = True

    def disable(self, reason: typing.Any):
        """
        Disables the plugin. The provided reason is used to inform users trying to use the plugin.

        :param reason: The reason for disabling the plugin, for example an exception message.
        """
        self._disabled = True
        self._disable_reason = str(reason)

    @property
    def ready(self):
        """Whether the plugin is ready for use. `False` for disabled plugins."""
        return self._initialized and not self._disabled

    @property
    def disabled(self):
        """Whether this plugin is disabled."""
        return self._disabled

    def get_disable_reason(self) -> typing.Optional[str]:
        """
        :return: The reason for disabling this plugin, or `None` if the plugin is not disabled.
        """
        if self.disabled:
            return self._disable_reason

    @property
    def module(self) -> str:
        """The module in which this plugin configuration is stored."""
        return self.__class__.__module__

    @property
    def package(self) -> str:
        """The package this plugin configuration covers."""
        return self.__class__.__module__.rsplit('.', 1)[0]
