"""
Process multiple MECA archives: parse them, generate deposition files, and send them to the Crossref API.

Main entrypoints are `parse(files, db)` which parses all given files to prepare for deposition and
`deposit(parsed_files, db)` which tries to deposit all given parsed files.
Both functions store detailed results in the given BatchDatabase and return an overview of the actions taken for each
given file.
"""

__all__ = [
    "deposit",
    "parse",
]

from datetime import datetime
from logging import getLogger
from pathlib import Path
from typing import List, Tuple

from mecadoi.article import Article, from_meca_manuscript
from mecadoi.crossref.api import deposit as deposit_file
from mecadoi.crossref.peer_review import generate_peer_review_deposition
from mecadoi.crossref.verify import VerificationResult, verify
from mecadoi.db import BatchDatabase, DepositionAttempt, ParsedFile
from mecadoi.dois import get_random_doi, get_free_doi
from mecadoi.meca import parse_meca_archive

LOGGER = getLogger(__name__)


def parse(files: List[str], db: BatchDatabase) -> List[ParsedFile]:
    """
    Parse all given files as MECA archives and store the results in `db`.

    If a file fails to parse, it is stored in the database with the status `ParsedFile.Invalid`.
    Files that are successfully parsed are stored with the status `ParsedFile.Valid` if they have a preprint DOI and
    reviews, with `ParsedFile.NoDoi` if they have a preprint DOI but no reviews, and with `ParsedFile.NoReviews` if they
    have reviews but no preprint DOI.
    Files that are successfully parsed but have the same preprint DOI as another file in the database are stored with
    the status `ParsedFile.Duplicate`.

    The modification time of each file is stored in the database as the time when the file was received.

    Args:
        files: A list of paths to potential MECA archives.
        db: The database to store the results in.

    Returns:
        A list of parsed files, including their status.
    """
    # Parse each file and register it in the batch database
    parsed_meca_archives = [
        _parse_potential_meca_archive(potential_meca_archive, db)
        for potential_meca_archive in sorted(files)
    ]
    db.insert_all(parsed_meca_archives)

    # Group the parsed files by their status
    return parsed_meca_archives


def _parse_potential_meca_archive(
    potential_meca_archive: str, db: BatchDatabase
) -> ParsedFile:
    received_at = _get_modification_time(potential_meca_archive)
    result = ParsedFile(path=potential_meca_archive, received_at=received_at)

    try:
        result.manuscript = parse_meca_archive(potential_meca_archive)
    except ValueError as e:
        LOGGER.info('Invalid MECA archive "%s": %s', potential_meca_archive, str(e))
        result.status = ParsedFile.Invalid
        return result

    result.doi = result.manuscript.preprint_doi
    if not result.doi:
        result.status = ParsedFile.NoDoi
    elif not result.manuscript.review_process:
        result.status = ParsedFile.NoReviews
    else:
        parsed_files_with_same_doi = db.fetch_parsed_files_with_doi(result.doi)
        is_duplicate = len(parsed_files_with_same_doi) > 0
        result.status = ParsedFile.Duplicate if is_duplicate else ParsedFile.Valid

    return result


def _get_modification_time(file_path: str) -> datetime:
    file = Path(file_path)
    mod_timestamp = file.stat().st_mtime
    return datetime.fromtimestamp(mod_timestamp)


def deposit(
    mecas: List[ParsedFile], db: BatchDatabase, dry_run: bool = True
) -> Tuple[List[DepositionAttempt], List[Article]]:
    """
    Generate deposition files from the given ParsedFiles, try to send the files to the Crossref API, and store the
    results in `db`.

    Raises a ValueError if not all given ParsedFiles are already stored in the database and have reviews as well as a
    preprint DOI.

    If the generation of a Crossref deposition file fails, the DepositionAttempt is stored in the database with the
    status `DepositionAttempt.GenerationFailed`.
    Before sending the deposition file to the Crossref API the file is verified by checking whether any review or reply
    already has a DOI assigned and whether all reviews and replies can be linked to.
    If this verification fails because a DOI is already present, the DepositionAttempt is stored in the database with
    the status `DepositionAttempt.DoisAlreadyPresent`. If the verification fails for any other reason,
    the DepositionAttempt is stored in the database with the status `DepositionAttempt.VerificationFailed`.
    When an error occurs while sending the deposition file to the Crossref API, the DepositionAttempt is stored in the
    database with the status `DepositionAttempt.Failed`.
    In any other case, the DepositionAttempt is stored in the database with the status `DepositionAttempt.Succeeded`.

    By default, nothing is actually sent to the Crossref API or stored in the database and only a dry run is executed.
    Set the `dry_run` parameter to False to actually do the depositions.

    Args:
        mecas: A list of ParsedFiles that contain MECA archives with reviews and a preprint DOI.
        db: The database to store the results in.
        dry_run: If True, don't actually send deposition files to the Crossref API and don't store the results in the
            database. Defaults to True.

    Returns:
        A tuple of a list of all deposition attempts and a list of articles that were successfully deposited.
    """
    if not all(
        [
            m.id
            and m.manuscript
            and m.manuscript.review_process
            and m.manuscript.preprint_doi
            for m in mecas
        ]
    ):
        raise ValueError(f"Not all required information present for all MECAs: {mecas}")

    def doi_generator(resource: str) -> str:
        if dry_run:
            return get_random_doi()
        return get_free_doi(db, resource)

    deposition_attempts = []
    successfully_deposited_articles = []
    for meca in mecas:
        deposition_attempt = DepositionAttempt(meca=meca, attempted_at=datetime.now())
        deposition_attempts.append(deposition_attempt)

        try:
            article = from_meca_manuscript(
                meca.manuscript,  # type: ignore[arg-type] # meca.manuscript is checked to be not None above
                meca.received_at,
                doi_generator,
            )
            deposition_attempt.deposition = generate_peer_review_deposition([article])
        except Exception as e:
            LOGGER.warning(
                'Failed to generate deposition file from "%s": %s', meca.path, str(e)
            )
            deposition_attempt.status = DepositionAttempt.GenerationFailed
            continue

        try:
            verification_result = verify(deposition_attempt.deposition)[0]
        except Exception as e:
            LOGGER.exception(e)
            LOGGER.error(deposition_attempt.deposition)
            verification_result = VerificationResult(
                preprint_doi=deposition_attempt.meca.path,
                error=str(e),
            )

        if verification_result.error:
            if verification_result.no_dois_assigned is False:
                deposition_attempt.status = DepositionAttempt.DoisAlreadyPresent
                LOGGER.info(
                    'DOIs already present for "%s": %s',
                    deposition_attempt.meca.path,
                    verification_result.error,
                )
            else:
                deposition_attempt.status = DepositionAttempt.VerificationFailed
                LOGGER.warning(
                    'Failed to verify deposition file from "%s": %s',
                    deposition_attempt.meca.path,
                    verification_result.error,
                )
            continue

        if dry_run:
            deposition_attempt.status = DepositionAttempt.Succeeded
            continue

        try:
            deposit_file(deposition_attempt.deposition)
            deposition_attempt.status = DepositionAttempt.Succeeded
        except Exception as e:
            LOGGER.warning(
                'Failed to deposit peer reviews from "%s": %s',
                deposition_attempt.meca.path,
                str(e),
            )
            deposition_attempt.status = DepositionAttempt.Failed

        if deposition_attempt.status == DepositionAttempt.Succeeded:
            successfully_deposited_articles.append(article)

    if not dry_run:
        db.insert_all(deposition_attempts)

    return (deposition_attempts, successfully_deposited_articles)
