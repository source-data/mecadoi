"""
Process multiple MECA archives: parse them, generate deposition files, and send them to the Crossref API.
"""

__all__ = [
    'batch_deposit',
    'BatchDepositRun',
]

from dataclasses import asdict, dataclass, field
from datetime import datetime
from os import makedirs
from pathlib import Path
from typing import List
from yaml import dump
from src.article import Article, from_meca_manuscript
from src.crossref.api import deposit as deposit_xml
from src.crossref.peer_review import generate_peer_review_deposition
from src.dois import get_free_doi
from src.meca import parse_meca_archive


@dataclass
class BatchDepositRun:
    timestamp: datetime

    invalid: List[str] = field(default_factory=list)
    incomplete: List[str] = field(default_factory=list)
    duplicate: List[str] = field(default_factory=list)

    processed: List[str] = field(default_factory=list)


def batch_deposit(input_dir: str, output_dir: str, verbose: int = 0, dry_run: bool = True) -> BatchDepositRun:
    """
    Generate deposition files and send them to the Crossref API for all peer reviews in the MECA archives found in the
    given input directory.
    """
    # find all .zips in the given input directory: these are the potential MECA archives
    potential_meca_archives = [str(file) for file in Path(input_dir).glob('*.zip')]

    timestamp = datetime.now()
    result = BatchDepositRun(timestamp=timestamp)
    processed_articles = []

    # Process each .zip and if it's a MECA with a preprint DOI and reviews, then generate deposition files for them
    for potential_meca_archive in potential_meca_archives:
        try:
            manuscript = parse_meca_archive(potential_meca_archive)
        except ValueError:
            result.invalid.append(potential_meca_archive)
            continue

        try:
            article = from_meca_manuscript(manuscript, timestamp, get_free_doi)
        except ValueError:
            result.incomplete.append(potential_meca_archive)
            continue

        deposition_xml = generate_peer_review_deposition(article)
        deposition_file_output_dir = f'{output_dir}/{article.doi}'
        try:
            makedirs(deposition_file_output_dir)
        except FileExistsError:
            result.duplicate.append(potential_meca_archive)
            continue

        deposition_file = f'{output_dir}/{article.doi}/deposition.xml'
        with open(deposition_file, 'w') as f:
            f.write(deposition_xml)

        if not dry_run:
            deposit_xml(deposition_xml, verbose=verbose)

        result.processed.append(potential_meca_archive)
        processed_articles.append(article)

    # Record the articles for which deposition files have been generated
    if processed_articles:
        processed_articles_output_dir = f'{output_dir}/processed-articles'
        try:
            makedirs(processed_articles_output_dir)
        except FileExistsError:
            pass
        export_processed_articles(f'{processed_articles_output_dir}/{timestamp}.yml', processed_articles)

    return result


def export_processed_articles(output_file: str, processed_articles: List[Article]) -> None:
    with open(f'{output_file}', 'w') as f:
        dump([asdict(processed_article) for processed_article in processed_articles], f)
