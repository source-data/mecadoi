import click
from yaml import dump
from src.cli.crossref.options import verbose_output
from src.batch import batch_generate, BatchGenerateRun


@click.command()
@click.argument(
    'input-directory',
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
@click.option(
    '-o', '--output-directory',
    required=True,
    type=click.Path(exists=True, file_okay=False, dir_okay=True, writable=True),
)
@verbose_output
@click.option(
    '--dry-run/--no-dry-run',
    default=True,
)
def generate(
    input_directory: str,
    output_directory: str,
    verbose: int,
    dry_run: bool,
) -> None:
    """
    Generate deposition files for all peer reviews in the MECA archives found in the given directory.
    """
    result = batch_generate(
        input_directory,
        output_directory,
        verbose=verbose,
        dry_run=dry_run,
    )
    click.echo(output(result), nl=False)


def output(batch_generate_run: BatchGenerateRun) -> str:
    return str(dump(batch_generate_run, canonical=False))
