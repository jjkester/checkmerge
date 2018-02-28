from checkmerge.app import CheckMerge
from checkmerge.cli import cli, click, error, pass_app, formatting
from checkmerge.parse import ParseError


@cli.command()
@click.option('--parser', '-p', 'parser', type=click.STRING, required=True,
              help="The parser to use. Run `list-parsers` to see the available parsers.")
@click.argument('base', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.argument('compared', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.argument('ancestor', required=False, type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@pass_app
def diff(app: CheckMerge, parser, base, compared, ancestor):
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

    # Set versions to diff
    versions = tuple(v for v in (base, compared, ancestor) if v is not None)

    # Do diff
    try:
        config = app.build_config()
        result = config.parse(*versions).diff().changes()
    except ParseError as e:
        return error(e)

    # Print changes
    formatter = formatting.CheckMergeFormatter()
    for change in sorted(result.changes, key=lambda c: c.sort_key):
        formatter.write_change(change)
    click.echo(formatter.getvalue(), nl=False)
