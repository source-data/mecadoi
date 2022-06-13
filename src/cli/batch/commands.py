import click
from yaml import dump
from src.cli.crossref.options import verbose_output
from src.batch import batch_deposit, BatchDepositRun


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
    result = batch_deposit(
        input_directory,
        output_directory,
        verbose=verbose,
        dry_run=dry_run,
    )
    click.echo(output(result), nl=False)


def output(batch_deposit_run: BatchDepositRun) -> str:
    return str(dump(batch_deposit_run, canonical=False))
