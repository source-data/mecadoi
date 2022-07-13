from dataclasses import asdict
from logging import getLogger
from os import mkdir, walk
from os.path import join
from shutil import move
from typing import Any, Dict
from uuid import uuid4
import click
from yaml import dump
from src.batch import deposit as batch_deposit, parse as batch_parse
from src.db import BatchDatabase

LOGGER = getLogger(__name__)


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
def parse(input_directory: str, output_directory: str) -> None:
    """
    Parse all files in the given directory, register them in the batch database, and move them to the given output
    directory.
    """
    LOGGER.debug('parse("%s", "%s")', input_directory, output_directory)

    # find all files in the given input directory: these are the potential MECA archives. Usually they're .zip files,
    # but let's just find everything in case they're not.
    input_files = [
        join(dirpath, filename)
        for dirpath, _, filenames in walk(input_directory)
        for filename in filenames
    ]
    LOGGER.debug('input_files=%s', input_files)

    # parse and register the input files
    result = batch_parse(input_files, BatchDatabase(f'{output_directory}/batch.sqlite3'))
    LOGGER.debug('result=%s', result)

    # move the input files to the output directory
    id_batch_run = str(uuid4())
    output_directory = f'{output_directory}/parsed/{id_batch_run}/'

    move(input_directory, output_directory)
    mkdir(input_directory)

    result_as_dict = asdict(result)
    result_as_dict['id'] = id_batch_run
    click.echo(output(result_as_dict), nl=False)

    LOGGER.info('Parsed and moved %s files from "%s" to "%s"', len(input_files), input_directory, output_directory)


@click.command()
@click.option(
    '-o', '--output-directory',
    required=True,
    type=click.Path(exists=True, file_okay=False, dir_okay=True, writable=True),
)
@click.option(
    '--dry-run/--no-dry-run',
    default=True,
)
def deposit(output_directory: str, dry_run: bool = True) -> None:
    """
    Find all files in the batch database that are not yet deposited, and try to deposit them.
    """
    batch_db = BatchDatabase(f'{output_directory}/batch.sqlite3')
    undeposited_files = batch_db.get_files_ready_for_deposition()
    deposition_results, successfully_deposited_articles = batch_deposit(undeposited_files, batch_db, dry_run=dry_run)

    result_as_dict = asdict(deposition_results)
    id_batch_run = str(uuid4())
    result_as_dict['id'] = id_batch_run
    result_as_dict['dry_run'] = dry_run

    if successfully_deposited_articles:
        deposition_output_directory = f'{output_directory}/deposited'
        mkdir(deposition_output_directory)
        with open(f'{deposition_output_directory}/{id_batch_run}.yml', 'w') as f:
            dump([asdict(article) for article in successfully_deposited_articles], f)

    click.echo(output(result_as_dict), nl=False)


def output(result: Dict[str, Any]) -> str:
    return str(dump(result, canonical=False))
