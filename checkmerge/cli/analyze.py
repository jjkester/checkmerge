import click

from checkmerge.app import CheckMerge
from checkmerge.cli import cli, error, pass_app
from checkmerge.parse import ParseError
from checkmerge.plugins import registry


@cli.command()
@click.option('--parser', '-p', 'parser', type=click.STRING, required=True,
              help="The parser to use. Run `list-parsers` to see the available parsers.")
@click.option('--analysis', '-a', 'analysis', type=click.STRING, multiple=True,
              help="The analysis to perform. Repeat this option to perform multiple analysis."
                   "Run `list-analysis` to see the available analysis.")
@click.argument('base', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.argument('compared', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@pass_app
def analyze(app: CheckMerge, parser, analysis, base, compared):
    """Analyze the differences between the given programs."""
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
        config = config.parse(base, compared).diff()
    except ParseError as e:
        return error(e)

    # Set up analysis
    for key in analysis:
        analysis_cls = registry.analysis.find(key)
        if analysis_cls is None:
            return error(f"No analysis with name '{key}' has been found.")
        else:
            config = config.analyze(analysis_cls)

    # Do analysis
    result = config.analysis()

    print(list(result))  # TODO Replace with reporting
