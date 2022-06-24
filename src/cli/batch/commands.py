from dataclasses import asdict
from logging import getLogger
from os import mkdir, walk
from os.path import join
from shutil import move
from typing import Any, Dict
from uuid import uuid4
import click
from yaml import dump
from src.batch import parse as batch_parse
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
    Parse all files in the given directory, register them in the database, and move them to the given output directory.
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
    output_directory = f'{output_directory}/{id_batch_run}/'

    move(input_directory, output_directory)
    mkdir(input_directory)

    result_as_dict = asdict(result)
    result_as_dict['id'] = id_batch_run
    click.echo(output(result_as_dict), nl=False)

    LOGGER.info('Parsed and moved %s files from "%s" to "%s"', len(input_files), input_directory, output_directory)


def output(result: Dict[str, Any]) -> str:
    return str(dump(result, canonical=False))
