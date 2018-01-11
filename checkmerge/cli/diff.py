import collections

from checkmerge.app import CheckMerge
from checkmerge.cli import click, cli, error
from checkmerge.diff.base import EditOperation


@cli.command()
@click.option('--parser', '-p', 'parser', type=click.STRING, required=True,
              help="The parser to use. Run `list-parsers` to see the available parsers.")
@click.argument('base', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.argument('compared', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.pass_context
def diff(ctx: click.Context, parser, base, compared):
    # Get app
    app: CheckMerge = ctx.ensure_object(CheckMerge)

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
        t1 = app.parse(base)
        t2 = app.parse(compared)
    except Exception as e:
        return error(e)

    result = app.diff(t1, t2)
    changes = result.reduced_changes

    op_sign = collections.defaultdict(lambda x: '??')
    op_sign.update({
        EditOperation.DELETE: '--',
        EditOperation.INSERT: '++',
    })
    op_color = collections.defaultdict(lambda x: 'black')
    op_color.update({
        EditOperation.DELETE: 'red',
        EditOperation.INSERT: 'green',
    })

    for old, new, op in changes:
        node = new if op == EditOperation.INSERT else old
        click.secho(f"@@{node.location}", color='cyan')
        click.secho(f"{op_sign[op]}{node}", color=op_color[op])
