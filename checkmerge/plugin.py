import typing

from checkmerge import analysis, plugins
from checkmerge.analysis.dependence import DependenceAnalysis
from checkmerge.analysis.reference import ReferenceAnalysis


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
            ReferenceAnalysis,
        ]
