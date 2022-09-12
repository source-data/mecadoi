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

from src.article import Article, from_meca_manuscript
from src.crossref.api import deposit as deposit_file
from src.crossref.peer_review import generate_peer_review_deposition
from src.crossref.verify import VerificationResult, verify
from src.db import BatchDatabase, DepositionAttempt, ParsedFile
from src.dois import get_random_doi, get_free_doi
from src.meca import parse_meca_archive

LOGGER = getLogger(__name__)


def parse(files: List[str], db: BatchDatabase) -> List[ParsedFile]:
    """
    Parse all given files as MECA archives and store the results in `db`.
    """
    # Parse each file and register it in the batch database
    parsed_meca_archives = [
        parse_potential_meca_archive(potential_meca_archive, db)
        for potential_meca_archive in sorted(files)
    ]
    db.insert_all(parsed_meca_archives)

    # Group the parsed files by their status
    return parsed_meca_archives


def parse_potential_meca_archive(
    potential_meca_archive: str, db: BatchDatabase
) -> ParsedFile:
    received_at = get_modification_time(potential_meca_archive)
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


def get_modification_time(file_path: str) -> datetime:
    file = Path(file_path)
    mod_timestamp = file.stat().st_mtime
    return datetime.fromtimestamp(mod_timestamp)


def deposit(
    mecas: List[ParsedFile], db: BatchDatabase, dry_run: bool = True
) -> Tuple[List[DepositionAttempt], List[Article]]:
    """
    Generate deposition files from the given MECAs, try to send the files to the Crossref API, and store the results in
    `db`.

    Raises a ValueError if not all given MECAs are already stored in the database and have reviews as well as a
    preprint DOI.
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
        deposition_attempt = DepositionAttempt(meca=meca)
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
            continue

        if deposition_attempt.deposition is None:
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
            LOGGER.warning(
                'Failed to verify deposition file from "%s": %s',
                deposition_attempt.meca.path,
                verification_result.error,
            )
            deposition_attempt.verification_failed = True
            continue
        else:
            deposition_attempt.verification_failed = False

        if dry_run:
            continue

        deposition_attempt.attempted_at = datetime.now()

        try:
            deposit_file(deposition_attempt.deposition)
            deposition_attempt.succeeded = True
        except Exception as e:
            LOGGER.warning(
                'Failed to deposit peer reviews from "%s": %s',
                deposition_attempt.meca.path,
                str(e),
            )
            deposition_attempt.succeeded = False

        if deposition_attempt.succeeded:
            successfully_deposited_articles.append(article)

    if not dry_run:
        db.insert_all(deposition_attempts)

    return (deposition_attempts, successfully_deposited_articles)
