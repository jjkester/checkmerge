import click

from checkmerge.analysis.report import AnalysisReport
from checkmerge.app import CheckMerge
from checkmerge.cli import cli, error, pass_app
from checkmerge.cli.formatting import CheckMergeFormatter
from checkmerge.parse import ParseError
from checkmerge.plugins import registry


@cli.command()
@click.option('--parser', '-p', 'parser', type=click.STRING, required=True,
              help="The parser to use. Run `list-parsers` to see the available parsers.")
@click.option('--analysis', '-a', 'analysis', type=click.STRING, required=True, multiple=True,
              help="The analysis to perform. Repeat this option to perform multiple analysis."
                   "Run `list-analysis` to see the available analysis.")
@click.argument('base', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.argument('compared', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.argument('ancestor', required=False, type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@pass_app
def analyze(app: CheckMerge, parser, analysis, base, compared, ancestor):
    """Analyze the differences between the given programs."""
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
        config = config.parse(*versions).diff()
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
    results = list(config.analysis())

    # Build report
    report = AnalysisReport(results)

    # Write report
    formatter = CheckMergeFormatter()
    formatter.write_report(report)
    click.echo(formatter.getvalue(), nl=False)


@cli.command()
@click.argument('test_dir', type=click.Path(exists=True, file_okay=False, resolve_path=True))
@click.argument('file_name', type=click.STRING)
@click.pass_context
def test(ctx: click.Context, file_name, test_dir):
    """Run a test. Finds the test files in the specified directory. The file name of the test must be relative to a
    version directory in the test directory."""
    ctx.invoke(analyze, parser='clang', analysis=['dependence', 'reference'], base=f"{test_dir}/a/{file_name}",
               compared=f"{test_dir}/b/{file_name}", ancestor=f"{test_dir}/0/{file_name}")
