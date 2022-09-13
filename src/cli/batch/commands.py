from datetime import datetime
from dateutil import parser
from dataclasses import asdict
from logging import getLogger
from os import mkdir, walk
from os.path import join
from shutil import move
from typing import Any, Dict, List, Optional
from uuid import uuid4
import click
from yaml import dump
from src.batch import deposit as batch_deposit, parse as batch_parse
from src.config import DB_URL
from src.db import BatchDatabase, DepositionAttempt, ParsedFile

LOGGER = getLogger(__name__)


@click.command()
@click.argument(
    "input-directory",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
@click.option(
    "-o",
    "--output-directory",
    required=True,
    type=click.Path(exists=True, file_okay=False, dir_okay=True, writable=True),
)
def parse(input_directory: str, output_directory: str) -> None:
    """
    Parse all files in the given directory, register them in the batch database, and move them to the given output
    directory.
    """
    LOGGER.debug('parse("%s", "%s")', input_directory, output_directory)

    # move the input files to the output directory
    id_batch_run = str(uuid4())
    output_directory = f"{output_directory}/parsed/{id_batch_run}/"

    move(input_directory, output_directory)
    mkdir(input_directory)

    # find all files in the output directory: these are the potential MECA archives. Usually they're .zip files,
    # but let's just find everything in case they're not.
    input_files = [
        join(dirpath, filename)
        for dirpath, _, filenames in walk(output_directory)
        for filename in filenames
    ]
    LOGGER.debug("input_files=%s", input_files)

    # parse and register the input files
    parsed_files = batch_parse(input_files, BatchDatabase(DB_URL))
    LOGGER.debug("parsed_files=%s", parsed_files)

    result = group_parsed_files_by_status(parsed_files)
    result["id"] = id_batch_run
    click.echo(output(result), nl=False)

    LOGGER.info(
        'Parsed and moved %s files from "%s" to "%s"',
        len(input_files),
        input_directory,
        output_directory,
    )


def group_parsed_files_by_status(meca_archives: List[ParsedFile]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}

    for meca_archive in meca_archives:
        resulting_list = None
        if meca_archive.manuscript is None:
            resulting_list = result.setdefault("invalid", [])
        elif not meca_archive.manuscript.review_process:
            resulting_list = result.setdefault("no_reviews", [])
        elif not meca_archive.manuscript.preprint_doi:
            resulting_list = result.setdefault("no_preprint_doi", [])
        else:
            resulting_list = result.setdefault("ready_for_deposition", [])
        resulting_list.append(get_name(meca_archive))

    return result


@click.command()
@click.option(
    "-o",
    "--output-directory",
    required=True,
    type=click.Path(exists=True, file_okay=False, dir_okay=True, writable=True),
)
@click.option(
    "--dry-run/--no-dry-run",
    default=True,
)
@click.option(
    "--retry-failed/--no-retry-failed",
    default=False,
)
@click.option("-a", "--after")
@click.option("-b", "--before")
def deposit(
    output_directory: str,
    dry_run: bool = True,
    retry_failed: bool = False,
    after: Optional[str] = None,
    before: Optional[str] = None,
) -> None:
    """
    Find all files in the batch database that are not yet deposited, and try to deposit them.
    """
    batch_db = BatchDatabase(DB_URL)
    after_as_datetime = parser.parse(after) if after is not None else datetime(1, 1, 1)
    before_as_datetime = parser.parse(before) if before is not None else datetime.now()
    
    files_to_deposit = (
        batch_db.get_files_to_retry_deposition(after=after_as_datetime, before=before_as_datetime)
        if retry_failed
        else batch_db.get_files_ready_for_deposition(after=after_as_datetime, before=before_as_datetime)
    )
    deposition_attempts, successfully_deposited_articles = batch_deposit(
        files_to_deposit, batch_db, dry_run=dry_run
    )

    result = group_deposition_attempts_by_status(deposition_attempts, dry_run=dry_run)
    id_batch_run = str(uuid4())
    result["id"] = id_batch_run
    result["dry_run"] = dry_run

    if successfully_deposited_articles:
        deposition_output_directory = f"{output_directory}/deposited"
        try:
            mkdir(deposition_output_directory)
        except FileExistsError:
            pass
        with open(f"{deposition_output_directory}/{id_batch_run}.yml", "w") as f:
            dump([asdict(article) for article in successfully_deposited_articles], f)

    click.echo(output(result), nl=False)


def group_deposition_attempts_by_status(
    deposition_attempts: List[DepositionAttempt], dry_run: bool
) -> Dict[str, Any]:
    result: Dict[str, Any] = {}

    for deposition_attempt in deposition_attempts:
        resulting_list = None
        if deposition_attempt.status == DepositionAttempt.GenerationFailed:
            resulting_list = result.setdefault("deposition_generation_failed", [])
        elif deposition_attempt.status == DepositionAttempt.DoisAlreadyPresent:
            resulting_list = result.setdefault("dois_already_present", [])
        elif deposition_attempt.status == DepositionAttempt.VerificationFailed:
            resulting_list = result.setdefault("deposition_verification_failed", [])
        elif deposition_attempt.status == DepositionAttempt.Succeeded:
            resulting_list = result.setdefault("deposition_succeeded", [])
        elif deposition_attempt.status == DepositionAttempt.Failed:
            resulting_list = result.setdefault("deposition_failed", [])
        else:
            resulting_list = result.setdefault("other", [])
        resulting_list.append(get_name(deposition_attempt.meca))

    return result


def get_name(parsed_file: ParsedFile) -> Any:
    if parsed_file.doi:
        return f"{parsed_file.path}|{parsed_file.doi}"
    return parsed_file.path


@click.command()
@click.option("-a", "--after")
@click.option("-b", "--before")
def ls(after: Optional[str] = None, before: Optional[str] = None) -> None:
    """
    List files in the batch database.
    """
    batch_db = BatchDatabase(DB_URL)
    after_as_datetime = parser.parse(after) if after is not None else datetime(1, 1, 1)
    before_as_datetime = parser.parse(before) if before is not None else datetime.now()
    parsed_files = batch_db.fetch_parsed_files_between(
        after_as_datetime, before_as_datetime
    )
    result_as_dict = group_parsed_files_by_status(parsed_files)

    click.echo(output(result_as_dict), nl=False)


def output(result: Dict[str, Any]) -> str:
    if any(result):
        return str(dump(result, canonical=False))
    return ""
