from datetime import datetime
from pathlib import Path
from dateutil import parser
from dataclasses import asdict
from logging import getLogger
from os import mkdir, remove, walk
from os.path import join
from shutil import move
from typing import Any, Dict, List, Optional
from uuid import uuid4
import click
from yaml import dump
from mecadoi.batch import deposit as batch_deposit, parse as batch_parse
from mecadoi.config import DB_URL
from mecadoi.db import BatchDatabase, DepositionAttempt, ParsedFile

LOGGER = getLogger(__name__)


@click.command()
@click.argument(
    "input-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
@click.option(
    "-o",
    "--output-dir",
    required=True,
    type=click.Path(exists=True, file_okay=False, dir_okay=True, writable=True),
    help="The directory to which processed files will be archived. Must be an existing directory.",
)
def parse(input_dir: str, output_dir: str) -> None:
    """
    Import files into the MECADOI database.

    The command archives all files in `INPUT_DIR` to a new folder in `--output-dir`, tries to parse
    them as MECA archives, and registers them in the MECADOI database.

    The processed files are moved to a subfolder named `parsed/<id>/` within `--output-dir`, where
    <id> is the unique ID generated for this command invocation.

    The ID of this command invocation and a list of all processed files is printed to stdout. The
    files are grouped by their status:

    \b
    - `invalid` for files that are not MECA archives (e.g. non-ZIP files)
    - `no_reviews` for MECA archives that contain no reviews or author replies
    - `no_preprint_doi` for MECA archives that contain no preprint DOI (required for DOI creation)
    - `ready_for_deposition` for MECA archives where review and author reply DOIs can be created
    """
    LOGGER.debug('parse("%s", "%s")', input_dir, output_dir)

    # move the input files to the output directory
    id_batch_run = str(uuid4())
    output_dir = f"{output_dir}/parsed/{id_batch_run}/"

    move(input_dir, output_dir)
    mkdir(input_dir)

    # find all files in the output directory: these are the potential MECA archives. Usually they're .zip files,
    # but let's just find everything in case they're not.
    input_files = [
        join(dirpath, filename)
        for dirpath, _, filenames in walk(output_dir)
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
        input_dir,
        output_dir,
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
    "--output-dir",
    required=True,
    type=click.Path(exists=True, file_okay=False, dir_okay=True, writable=True),
    help="The directory to which a file with information about successful deposition attempts is written.",
)
@click.option(
    "--dry-run/--no-dry-run",
    default=True,
    help="Only show what would happen / actually create DOIs and update the database. DEFAULT: `--dry-run`",
)
@click.option(
    "--retry-failed/--no-retry-failed",
    default=False,
    help=(
        "Re-try DOI deposition for MECA archives for which a previous attempt has failed / "
        "deposit DOIs for MECA archives without deposition attempt. DEFAULT: `--no-retry-failed`"
    ),
)
@click.option(
    "-a",
    "--after",
    help="Only attempt to deposit DOIs for MECA archives that were received after this date. Example: 2022-04-01",
)
@click.option(
    "-b",
    "--before",
    help="Only attempt to deposit DOIs for MECA archives that were received before this date. Example: 2022-10-01",
)
def deposit(
    output_dir: str,
    dry_run: bool = True,
    retry_failed: bool = False,
    after: Optional[str] = None,
    before: Optional[str] = None,
) -> None:
    """
    Create DOIs for MECA archives in the MECADOI database.

    The command finds those MECA archives in the MECADOI database for which DOIs can be deposited,
    i.e. those that have reviews and a preprint DOI and for which no deposition has been attempted
    yet.
    Then a deposition attempt is made for each selected MECA and its result recorded in the MECADOI
    database.
    Information about each successful deposition attempt is written to a file in `--output-dir`.

    DOIs are deposited by sending an XML file conforming to the Crossref metadata schema to the
    Crossref API.
    Emails with detailed information about the status of every submission is sent to the depositor's
    email address, which is taken from the `DEPOSITOR_EMAIL` variable in your `.env` file.
    Failures in the deposition data (e.g. malformed DOIs) are only reported in this email, i.e. this
    command almost always executes successfully.

    Before a deposition is attempted the DOIs to be created are verified against the EEB platform
    (eeb.embo.org).
    If any review or reply already has a DOI, or if the amount of reviews and replies don't match
    exactly, the attempt is marked as failed.

    The ID of this command invocation and a list of all processed MECA archives is printed to stdout.
    The MECA archives are grouped by their status:

    \b
    - `deposition_generation_failed` if the Crossref XML file could not be generated
    - `dois_already_present` if at least one review or reply in the MECA archive already has a DOI
    - `deposition_verification_failed`  if the reviews and replies in the MECA archive don't exactly match those on EEB
    - `deposition_succeeded` if the deposition XML was accepted by the Crossref API
    - `deposition_failed` if the deposition XML was not accepted by or could not be sent to the Crossref API

    NOTE: By default, this command will *not* create any DOIs or update the MECADOI database. Pass
    the `--no-dry-run` option to actually execute the irreversible deposition and update the database.
    """
    batch_db = BatchDatabase(DB_URL)
    after_as_datetime = parser.parse(after) if after is not None else datetime(1, 1, 1)
    before_as_datetime = parser.parse(before) if before is not None else datetime.now()

    files_to_deposit = (
        batch_db.get_files_to_retry_deposition(
            after=after_as_datetime, before=before_as_datetime
        )
        if retry_failed
        else batch_db.get_files_ready_for_deposition(
            after=after_as_datetime, before=before_as_datetime
        )
    )
    deposition_attempts, successfully_deposited_articles = batch_deposit(
        files_to_deposit, batch_db, dry_run=dry_run
    )

    result = group_deposition_attempts_by_status(deposition_attempts, dry_run=dry_run)
    id_batch_run = str(uuid4())
    result["id"] = id_batch_run
    result["dry_run"] = dry_run

    if successfully_deposited_articles:
        deposition_output_dir = f"{output_dir}/deposited"
        try:
            mkdir(deposition_output_dir)
        except FileExistsError:
            pass
        with open(f"{deposition_output_dir}/{id_batch_run}.yml", "w") as f:
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


@click.command(hidden=True)
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


@click.command()
@click.option(
    "--dry-run/--no-dry-run",
    default=True,
    help="Only show what would happen / actually delete MECA archives. DEFAULT: `--dry-run`",
)
def prune(dry_run: bool = True) -> None:
    """
    Delete MECA archives that are no longer needed for deposition.

    All MECA archives are parsed during the initial import and all information necessary for DOI
    creation is stored in the MECADOI database. After this step, the actual file on disk is no
    longer needed to create DOIs.

    This command checks the file path of every MECA archive registered in the MECADOI database and
    deletes those files that exist on disk.

    NOTE: By default, this command will *not* delete any files. Pass the `--no-dry-run` option to
    actually execute the deletions.
    """
    batch_db = BatchDatabase(DB_URL)
    to_delete = set(
        [path for path in batch_db.fetch_all(ParsedFile.path) if Path(path).exists()]
    )

    deletion_failed = set()
    if not dry_run:
        for path in to_delete:
            try:
                remove(path)
            except Exception as e:
                LOGGER.warning('Pruning "%s" failed with "%s"', path, str(e))
                deletion_failed.add(path)
    deleted = to_delete - deletion_failed

    result: Dict[str, Any] = {"dry_run": dry_run}
    if deleted:
        result["deleted"] = list(sorted(deleted))
    if deletion_failed:
        result["failed"] = list(sorted(deletion_failed))

    click.echo(output(result), nl=False)
