from checkmerge.cli import click, cli
from checkmerge.plugins import registry


class PluginDataFormatter(click.HelpFormatter):
    def write_plugin_obj(self, obj, extra=None):
        with self.section(f"{obj.name} ({obj.key})"):
            self.write_text(f"{obj.description}")
            if extra:
                self.write_paragraph()
                self.write_text(extra)


@cli.command('list-plugins')
@click.option('--disabled', is_flag=True, default=False, help="Show disabled plugins.")
def list_plugins(disabled):
    """Lists the available plugins."""
    all_plugins = [plugin for plugin in registry.registry.values()]
    enabled_plugins = [plugin for plugin in all_plugins if not plugin.disabled]
    disabled_plugins = [plugin for plugin in all_plugins if plugin.disabled]
    plugins = disabled_plugins if disabled else enabled_plugins

    if all_plugins:
        formatter = PluginDataFormatter()
        indent = formatter.indent_increment * ' '

        formatter.write_dl((
            ("Found plugins:", str(len(all_plugins))),
            (f"{indent}Enabled:", str(len(enabled_plugins))),
            (f"{indent}Disabled:", str(len(disabled_plugins))))
        )

        for plugin in plugins:
            if disabled:
                formatter.write_plugin_obj(plugin, f"Disable reason: {plugin._disable_reason}")
            else:
                formatter.write_plugin_obj(plugin)

        if not disabled:
            formatter.write_paragraph()
            formatter.write_text(f"Run this command with '--disabled' to see the disabled plugins.")

        click.echo(formatter.getvalue(), nl=False)
    else:
        if len(all_plugins) > 0:
            click.echo("No disabled plugins.")
        elif disabled:
            click.echo("No plugins loaded. Run again with --disabled to check for disabled plugins.")
        else:
            click.echo("No plugins available. Please check your PYTHONPATH.")


@cli.command('list-parsers')
def list_parsers():
    """Lists the available parsers."""
    parsers = registry.parsers.all()

    if parsers:
        formatter = PluginDataFormatter()
        indent = formatter.indent_increment * ' '

        formatter.write_text(f"Available parsers:{indent}{len(parsers)}")

        for parser in parsers:
            formatter.write_plugin_obj(parser)

        click.echo(formatter.getvalue(), nl=False)
    else:
        click.echo("No parsers available. Run 'list-plugins --disabled' to see the disabled plugins.")


@cli.command('list-analysis')
def list_analysis():
    """Lists the available analysis algorithms."""
    analysis = registry.analysis.all()

    if analysis:
        formatter = PluginDataFormatter()
        indent = formatter.indent_increment * ' '

        formatter.write_text(f"Available analysis algorithms:{indent}{len(analysis)}")

        for algorithm in analysis:
            formatter.write_plugin_obj(algorithm)

        click.echo(formatter.getvalue(), nl=False)
    else:
        click.echo("No analysis algorithms available. Run 'list-plugins --disabled' to see the disabled plugins.")
