import typing

from checkmerge import plugins, analysis
from checkmerge.analysis.dependence import DependenceAnalysis


class CheckMergePlugin(plugins.Plugin):
    """
    The default CheckMerge "plugin".
    """
    key = 'default'
    name = "CheckMerge"
    description = "The native CheckMerge plugin."

    def provide_analysis(self) -> typing.List[typing.Type[analysis.Analysis]]:
        return [
            DependenceAnalysis,
        ]
