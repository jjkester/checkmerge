from checkmerge import plugins
from checkmerge_clang.clang import configure


class ClangPlugin(plugins.Plugin):
    """
    Configuration of the CheckMerge Clang plugin.
    """
    key = 'clang'
    name = "Clang support"
    description = "Provides support for the C language through libclang."

    def provide_parsers(self):
        from checkmerge_clang.parse import ClangParser
        return [ClangParser]

    def setup(self):
        configure()
        super(ClangPlugin, self).setup()
