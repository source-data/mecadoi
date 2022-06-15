"""
Process multiple MECA archives: parse them, generate deposition files, and send them to the Crossref API.
"""

__all__ = [
    'batch_deposit',
    'BatchDepositRun',
    'DepositionResult',
    'MecaDeposition',
    'MecaParsingResult',
]

from dataclasses import asdict, dataclass
from datetime import datetime
from os import makedirs, remove
from pathlib import Path
from typing import List, Optional, Tuple, Union
from yaml import dump
from src.article import Article, from_meca_manuscript
from src.crossref.api import deposit as deposit_xml
from src.crossref.peer_review import generate_peer_review_deposition
from src.dois import get_free_doi
from src.meca import parse_meca_archive


@dataclass
class DepositionResult:
    output: Union[str, None] = None
    error: Union[str, None] = None


@dataclass
class MecaParsingResult:
    input: str
    error: Union[str, None] = None
    has_reviews: Union[bool, None] = None
    has_preprint_doi: Union[bool, None] = None
    doi_already_processed: Union[bool, None] = None


@dataclass
class MecaDeposition:
    meca_parsing: MecaParsingResult
    deposition_file_generation: Union[DepositionResult, None] = None
    crossref_deposition: Union[DepositionResult, None] = None


@dataclass
class BatchDepositRun:
    results: List[MecaDeposition]
    timestamp: datetime


def batch_deposit(input_dir: str, output_dir: str, verbose: int = 0, dry_run: bool = True) -> BatchDepositRun:
    """
    Generate deposition files and send them to the Crossref API for all peer reviews in the MECA archives found in the
    given input directory.
    """
    # find all .zips in the given input directory: these are the potential MECA archives
    zips = [file for file in Path(input_dir).glob('*.zip')]

    # Process each .zip and if it's a MECA with a preprint DOI and reviews, then generate and deposit DOIs for them
    timestamp = datetime.now()
    batch_deposit_run = BatchDepositRun(timestamp=timestamp, results=[])
    processed_articles = []
    for zip_file in zips:
        result, processed_article = process(zip_file, output_dir, verbose, dry_run)
        batch_deposit_run.results.append(result)
        if processed_article:
            processed_articles.append(processed_article)

    for zip_file in zips:
        remove(zip_file)

    if processed_articles:
        processed_articles_output_dir = f'{output_dir}/processed-articles'
        try:
            makedirs(processed_articles_output_dir)
        except FileExistsError:
            pass
        export_processed_articles(f'{processed_articles_output_dir}/{timestamp}.yml', processed_articles)

    return batch_deposit_run


def process(
    zip_file: Path,
    output_base_dir: str,
    verbose: int,
    dry_run: bool,
) -> Tuple[MecaDeposition, Optional[Article]]:
    result = MecaDeposition(meca_parsing=MecaParsingResult(input=str(zip_file)))

    try:
        manuscript = parse_meca_archive(zip_file)
    except ValueError as e:
        result.meca_parsing.error = str(e)
        return result, None

    result.meca_parsing.has_reviews = True if manuscript.review_process else False
    result.meca_parsing.has_preprint_doi = True if manuscript.preprint_doi is not None else False
    if not (result.meca_parsing.has_reviews and result.meca_parsing.has_preprint_doi):
        return result, None

    publication_date = datetime.now()
    article = from_meca_manuscript(manuscript, publication_date, get_free_doi)

    output_dir = f'{output_base_dir}/{article.doi}'
    try:
        makedirs(output_dir)
        result.meca_parsing.doi_already_processed = False
    except FileExistsError:
        result.meca_parsing.doi_already_processed = True
        return result, None

    result.deposition_file_generation = DepositionResult()
    try:
        deposition_xml = generate_peer_review_deposition(article)
        deposition_file = f'{output_dir}/deposition.xml'
        with open(deposition_file, 'w') as f:
            f.write(deposition_xml)
        result.deposition_file_generation.output = deposition_file
    except Exception as e:
        result.deposition_file_generation.error = str(e)
        return result, None

    if dry_run:
        return result, None

    result.crossref_deposition = DepositionResult()

    try:
        response = deposit_xml(deposition_xml, verbose=verbose)
        result.crossref_deposition.output = response
    except Exception as e:
        result.crossref_deposition.error = str(e)
        return result, None

    return result, article


def export_processed_articles(output_file: str, processed_articles: List[Article]) -> None:
    with open(f'{output_file}', 'w') as f:
        dump([asdict(processed_article) for processed_article in processed_articles], f)
