from dataclasses import dataclass
from datetime import datetime
from os import makedirs
from pathlib import Path
from typing import List
from src.meca import MECArchive
from src.crossref import deposit as deposit_xml, generate_peer_review_deposition


@dataclass
class DepositionResult:
    output: object = None
    error: str = None


@dataclass
class MecaParsingResult:
    input: str
    error: str = None
    has_reviews: bool = None
    has_preprint_doi: bool = None
    doi_already_processed: bool = None


@dataclass
class MecaDeposition:
    meca_parsing: MecaParsingResult
    depositition_file_generation: DepositionResult = None
    crossref_deposition: DepositionResult = None


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
            process(zip, output_directory, verbose, strict_validation, dry_run)
            for zip in zips
        ],
    )
    return batch_deposit_run


def process(
    zip_file,
    output_base_dir: str,
    verbose: int,
    strict_validation: bool,
    dry_run: bool,
) -> MecaDeposition:
    result = MecaDeposition(meca_parsing=MecaParsingResult(input=str(zip_file)))

    try:
        meca = MECArchive(zip_file, strict_validation=strict_validation)
    except ValueError as e:
        result.meca_parsing.error = str(e)
        return result

    result.meca_parsing.has_reviews = True if meca.reviews else False
    result.meca_parsing.has_preprint_doi = True if meca.article_preprint_doi else False
    if not (result.meca_parsing.has_reviews and result.meca_parsing.has_preprint_doi):
        return result

    output_dir = f'{output_base_dir}/{meca.article_preprint_doi}'

    try:
        makedirs(output_dir)
        result.meca_parsing.doi_already_processed = False
    except FileExistsError:
        result.meca_parsing.doi_already_processed = True
        return result

    result.depositition_file_generation = DepositionResult()
    try:
        deposition_xml = generate_peer_review_deposition(meca)
        deposition_file = f'{output_dir}/deposition.xml'
        with open(deposition_file, 'w') as f:
            f.write(deposition_xml.decode("utf-8"))
        result.depositition_file_generation.output = deposition_file
    except Exception as e:
        result.depositition_file_generation.error = str(e)
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
