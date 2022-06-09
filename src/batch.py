""""""

__all__ = [
    'batch_generate',
    'BatchGenerateRun',
    'DepositionResult',
    'DepositionFileGenerationResult',
    'MecaParsingResult',
]

from dataclasses import dataclass
from datetime import datetime
from os import makedirs
from pathlib import Path
from shutil import move
from typing import List, Union
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
class DepositionFileGenerationResult:
    meca_parsing: MecaParsingResult
    deposition_file_generation: Union[DepositionResult, None] = None


@dataclass
class BatchGenerateRun:
    results: List[DepositionFileGenerationResult]
    timestamp: datetime


def batch_generate(
    input_directory: str,
    output_directory: str,
    verbose: int = 0,
    dry_run: bool = True,
) -> BatchGenerateRun:
    """
    Generate deposition files for all peer reviews in the MECA archives found in the given directory.
    """
    # find all .zips in the given input directory: these are the potential MECA archives
    zips = [file for file in Path(input_directory).glob('*.zip')]

    # Process each .zip and if it's a MECA with a preprint DOI and reviews, then generate deposition files for them
    timestamp = datetime.now()
    batch_generate_run = BatchGenerateRun(
        timestamp=timestamp,
        results=[
            process(zip, output_directory, verbose, dry_run)
            for zip in zips
        ],
    )

    # Move all processed files to an archive directory
    meca_archive_dir = f'{output_directory}/archive/{timestamp.timestamp()}/'
    makedirs(meca_archive_dir)
    for processed_meca in zips:
        move(processed_meca, meca_archive_dir)

    return batch_generate_run


def process(
    zip_file: Path,
    output_base_dir: str,
    verbose: int,
    dry_run: bool,
) -> DepositionFileGenerationResult:
    result = DepositionFileGenerationResult(meca_parsing=MecaParsingResult(input=str(zip_file)))

    try:
        article = parse_meca_archive(zip_file)
    except ValueError as e:
        result.meca_parsing.error = str(e)
        return result

    result.meca_parsing.has_reviews = True if article.review_process else False
    result.meca_parsing.has_preprint_doi = True if article.preprint_doi is not None else False
    if not (result.meca_parsing.has_reviews and result.meca_parsing.has_preprint_doi):
        return result

    output_dir = f'{output_base_dir}/{article.preprint_doi}'

    try:
        makedirs(output_dir)
        result.meca_parsing.doi_already_processed = False
    except FileExistsError:
        result.meca_parsing.doi_already_processed = True
        return result

    result.deposition_file_generation = DepositionResult()
    try:
        publication_date = datetime.now()
        deposition_xml = generate_peer_review_deposition(article, publication_date, get_free_doi)
        deposition_file = f'{output_dir}/deposition.xml'
        with open(deposition_file, 'w') as f:
            f.write(deposition_xml.decode("utf-8"))
        result.deposition_file_generation.output = deposition_file
    except Exception as e:
        result.deposition_file_generation.error = str(e)

    return result
