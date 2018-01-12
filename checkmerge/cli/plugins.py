from checkmerge.cli import click, cli
from checkmerge.plugins import registry


@cli.command('list-plugins')
@click.option('--disabled', is_flag=True, default=False, help="Show disabled plugins.")
def list_plugins(disabled):
    """Lists the available plugins."""
    all_plugins = [registry.get_instance(plugin) for plugin in registry.registry.values()]
    plugins = [plugin for plugin in all_plugins if plugin.disabled is disabled]

    if plugins:
        for plugin in plugins:
            click.echo(f"{plugin.name}: {plugin.description}")
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
        for parser in parsers:
            click.echo(f"{parser.key}")
    else:
        click.echo("No parsers available. Check your plugin overview for details.")
