from checkmerge import plugins


class CheckMergePlugin(plugins.Plugin):
    """
    The default CheckMerge "plugin".
    """
    key = 'default'
    name = "CheckMerge"
    description = "The native CheckMerge plugin."
