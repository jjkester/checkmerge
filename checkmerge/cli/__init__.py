import click

from checkmerge.app import CheckMerge
from checkmerge.plugins import registry


def print_version(ctx, param, value):
    """CLI option callback that prints the version information and exits."""
    if not value or ctx.resilient_parsing:
        return
    click.secho(f"CheckMerge {CheckMerge.version} ({CheckMerge.build})", bold=True)
    click.secho(CheckMerge.platform)
    ctx.exit()


def print_plugins(ctx, param, value):
    """CLI option callback that prints the plugin information and exits."""
    if not value or ctx.resilient_parsing:
        return

    plugins = registry.registry.values()
    active = sum(1 for _ in filter(lambda x: not x.disabled, plugins))
    disabled = sum(1 for _ in filter(lambda x: x.disabled, plugins))

    if plugins:
        click.secho(f"Available plugins ({len(plugins)} total, {active} active and {disabled} disabled):", bold=True)
        for plugin in map(registry.get_instance, sorted(plugins, key=lambda x: x.name)):
            if plugin.disabled:
                click.secho(f"  X {plugin.name} ({plugin.key}): {plugin.description}", fg='red')
                click.secho(f"    DISABLED: {plugin._disable_reason}", fg='red')
            else:
                click.secho(f"  - {plugin.name} ({plugin.key}): {plugin.description}", fg='green')
                click.secho(f"    LOADED", fg='green')
    else:
        click.secho("No plugins loaded!", fg='red')
    ctx.exit()


pass_app = click.make_pass_decorator(CheckMerge)


@click.group('checkmerge')
@click.option('--version', is_flag=True, callback=print_version, expose_value=False, is_eager=True,
              help="Print the current version and exit.")
@click.option('--plugins', is_flag=True, callback=print_plugins, expose_value=False, is_eager=True,
              help="Print the available plugins and exit.")
@click.pass_context
def cli(ctx: click.Context) -> None:
    ctx.obj = CheckMerge()


def main():
    """Main method of the CLI."""
    CheckMerge.setup()
    cli(prog_name=cli.name)
