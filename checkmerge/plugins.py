import importlib
import os
import typing

import sys

from checkmerge import parse
from checkmerge.util.registry import Registry


class KeyRegistry(Registry):
    """
    Registry for classes with a `key` class parameter.
    """
    def key(self, cls):
        return cls.key


class PluginRegistry(Registry[str, typing.Type["Plugin"]]):
    """
    Manages the available CheckMerge plugins.
    """
    def __init__(self):
        super(PluginRegistry, self).__init__()
        self.instances: typing.Dict[typing.Type["Plugin"], "Plugin"] = {}
        self.parsers: Registry[str, parse.Parser] = KeyRegistry()

    def key(self, cls: typing.Type["Plugin"]) -> str:
        return cls.key

    def setup(self):
        """
        Sets up the registered plugins. Marks plugins with errors as disabled. Registers functionality from the plugins
        in the appropriate sub registers.
        """
        for plugin_class in self.registry.values():
            if plugin_class in self.instances:
                continue

            plugin = plugin_class()

            # Try to setup plugin, disable if an error occurs
            try:
                plugin.setup()
            except Exception as e:
                plugin.disable(reason=str(e))

            # Register plugin instance
            self.instances[plugin_class] = plugin

            # Pull functions from plugin
            if plugin.ready:
                for parser in plugin.provide_parsers():
                    self.parsers.register(parser)

    def _filter(self, item: "Plugin") -> bool:
        return not item.disabled

    def get_instance(self, cls: typing.Type["Plugin"]) -> typing.Optional["Plugin"]:
        """
        Returns the instance of the given plugin class if the plugin has been setup.

        :param cls: The plugin class to get the instance for.
        :return: The plugin class instance.
        """
        return self.instances.get(cls, None)


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

    def provide_parsers(self) -> typing.List[parse.Parser]:
        """
        Returns a list of the parsers provided by this plugin.

        :return: The parsers provided by this plugin.
        """
        return []

    def setup(self):
        """
        Performs plugin initialization before it is used.
        """
        self._initialized = True

    def disable(self, reason: str):
        """
        Disables the plugin.
        """
        self._disabled = True
        self._disable_reason = reason

    @property
    def ready(self):
        return self._initialized and not self._disabled

    @property
    def disabled(self):
        return self._disabled

    @property
    def module(self):
        return self.__class__.__module__
