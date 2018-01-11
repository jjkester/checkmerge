import importlib
import os

import click

from checkmerge.app import CheckMerge


pass_app = click.make_pass_decorator(CheckMerge)


@click.group()
@click.pass_context
def cli(ctx: click.Context) -> None:
    """CheckMerge is a tool for analyzing code merges for possible merge problems."""
    ctx.obj = CheckMerge()


@cli.command()
def version():
    """Print the program version and platform information."""
    click.echo(f"CheckMerge {CheckMerge.version} ({CheckMerge.build})")
    click.echo(CheckMerge.platform)


@cli.command()
def docs():
    """Open the documentation in a web browser."""
    formatter = click.HelpFormatter()
    with formatter.section("Documentation"):
        formatter.write_text(CheckMerge.docs)
    with formatter.section("Repository and bug tracker"):
        formatter.write_text(CheckMerge.repo)
    click.echo(formatter.getvalue(), nl=False)


def find_commands():
    """Finds commands for the CLI."""
    for file in os.listdir(os.path.dirname(__file__)):
        if not file.startswith('_') and file.endswith('.py'):
            importlib.import_module('{}.{}'.format(__name__, file[:-3]))


def main():
    """Main method of the CLI."""
    CheckMerge.setup()
    find_commands()
    cli(prog_name="checkmerge")


def error(msg, code=-1):
    click.echo(f"Error: {msg}", err=True)
    click.get_current_context().exit(code)
