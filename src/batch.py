"""
Process multiple MECA archives: parse them, generate deposition files, and send them to the Crossref API.

Main entrypoint is parse(files, db) which parses all given files and stores the results in the given BatchDatabase.
"""

__all__ = [
    'parse',
    'ParsedFiles',
]

from dataclasses import dataclass, field
from datetime import datetime
from logging import getLogger
from pathlib import Path
from typing import List, Tuple
from src.db import BatchDatabase, ParsedFile
from src.meca import parse_meca_archive

LOGGER = getLogger(__name__)


@dataclass
class ParsedFiles:
    """The files that were parsed in one batch-parsing run."""

    invalid: List[str] = field(default_factory=list)
    """These files are either not .zip files or invalid MECA archives."""

    no_reviews: List[str] = field(default_factory=list)
    """These MECA archives contain no reviews."""

    no_preprint_doi: List[str] = field(default_factory=list)
    """These MECA archives don't have a DOI for the preprint that their manuscript is based on."""

    ready_for_deposition: List[str] = field(default_factory=list)
    """These MECA archives have all the necessary information to proceed with review DOI deposition."""


def parse(files: List[str], db: BatchDatabase) -> ParsedFiles:
    """
    Parse all given files as MECA archives and store the results in `db`.
    """
    # Parse each file and register it in the batch database
    parsed_meca_archives = [
        parse_potential_meca_archive(potential_meca_archive)
        for potential_meca_archive in files
    ]
    db.add_parsed_files(parsed_meca_archives)

    # Group the parsed files by their status
    invalid, no_reviews, no_preprint_doi, ready_for_deposition = partition_meca_archives(parsed_meca_archives)
    return ParsedFiles(
        invalid=invalid,
        no_reviews=no_reviews,
        no_preprint_doi=no_preprint_doi,
        ready_for_deposition=ready_for_deposition,
    )


def partition_meca_archives(meca_archives: List[ParsedFile]) -> Tuple[List[str], List[str], List[str], List[str]]:
    invalid: List[str] = []
    no_reviews: List[str] = []
    no_preprint_doi: List[str] = []
    ready_for_deposition: List[str] = []

    for meca_archive in meca_archives:
        resulting_list = None
        if meca_archive.manuscript is None:
            resulting_list = invalid
        elif not meca_archive.manuscript.review_process:
            resulting_list = no_reviews
        elif not meca_archive.manuscript.preprint_doi:
            resulting_list = no_preprint_doi
        else:
            resulting_list = ready_for_deposition
        resulting_list.append(meca_archive.path)

    return (invalid, no_reviews, no_preprint_doi, ready_for_deposition)


def parse_potential_meca_archive(potential_meca_archive: str) -> ParsedFile:
    received_at = get_modification_time(potential_meca_archive)
    result = ParsedFile(path=potential_meca_archive, received_at=received_at)

    try:
        result.manuscript = parse_meca_archive(potential_meca_archive)
    except ValueError as e:
        LOGGER.info('Invalid MECA archive "%s": %s', potential_meca_archive, str(e))
        return result

    return result


def get_modification_time(file_path: str) -> datetime:
    file = Path(file_path)
    mod_timestamp = file.stat().st_mtime
    return datetime.fromtimestamp(mod_timestamp)
