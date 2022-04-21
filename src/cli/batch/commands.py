import click
import yaml

from src.cli.crossref.options import verbose_output
from src.cli.meca.options import strict_validation
from src.batch import batch_deposit, BatchDepositRun


@click.command()
@click.argument(
    'input-directory',
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
@verbose_output
@strict_validation
@click.option(
    '--dry-run/--no-dry-run',
    default=True,
)
def deposit(
    input_directory,
    verbose: int,
    strict_validation: bool,
    dry_run: bool,
):
    """
    Deposit DOIs for all peer reviews in the MECA archives found in the given directory.
    """
    result = batch_deposit(
        input_directory,
        verbose=verbose,
        strict_validation=strict_validation,
        dry_run=dry_run,
    )
    click.echo(output(result))


def output(batch_deposit_run: BatchDepositRun) -> str:
    return yaml.dump(batch_deposit_run, canonical=False)
