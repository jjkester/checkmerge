from checkmerge.app import CheckMerge
from checkmerge.cli import cli, click, error, pass_app, formatting
from checkmerge.parse import ParseError


@cli.command()
@click.option('--parser', '-p', 'parser', type=click.STRING, required=True,
              help="The parser to use. Run `list-parsers` to see the available parsers.")
@click.argument('base', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.argument('compared', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@pass_app
def diff(app: CheckMerge, parser, base, compared):
    """Calculate and output the differences between the given programs.

    The difference between the programs is calculated using the CheckMerge abstract syntax tree (AST) based diff
    algorithm."""
    # Set parser
    try:
        app.parser = parser
    except ValueError as e:
        return error(e)

    # Some checks
    if app.parser is None or app.diff_algorithm is None:
        return error("Unexpected configuration error.")

    # Do diff
    try:
        config = app.build_config()
        result = config.parse(base, compared).diff().changes()
    except ParseError as e:
        return error(e)

    # Print changes
    for change in sorted(result.reduced_changes, key=lambda c: c.sort_key):
        text = formatting.format_change(change)
        if text:
            click.echo(text)
