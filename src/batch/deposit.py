from dataclasses import dataclass
from datetime import datetime
from os import makedirs
from pathlib import Path
from typing import List, Union
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


def batch_deposit(
    input_directory: str,
    output_directory: str,
    verbose: int = 0,
    strict_validation: bool = True,
    dry_run: bool = True,
) -> BatchDepositRun:
    """
    Deposit DOIs for all peer reviews in the MECA archives found in the given directory.
    """
    # find all MECA archives in the given input directory whose peer reviews can be deposited
    zips = Path(input_directory).glob('*.zip')
    batch_deposit_run = BatchDepositRun(
        timestamp=datetime.now(),
        results=[
            process(zip, output_directory, verbose, dry_run)
            for zip in zips
        ],
    )
    return batch_deposit_run


def process(
    zip_file: Path,
    output_base_dir: str,
    verbose: int,
    dry_run: bool,
) -> MecaDeposition:
    result = MecaDeposition(meca_parsing=MecaParsingResult(input=str(zip_file)))

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

    if dry_run:
        return result

    result.crossref_deposition = DepositionResult()

    try:
        response = deposit_xml(deposition_xml, verbose=verbose)
        result.crossref_deposition.output = response
    except Exception as e:
        result.crossref_deposition.error = str(e)
        return result

    return result
