from dataclasses import dataclass
from typing import BinaryIO, Dict, List, Optional, Union
from xsdata.formats.dataclass.parsers import XmlParser
from src.crossref.xml.doi_batch import DoiBatch, PeerReview
from src.eeb.api import get_articles


@dataclass
class VerificationResult:
    preprint_doi: str
    all_reviews_present: Optional[bool]
    error: Optional[str]


def verify(deposition_file: Union[str, bytes, BinaryIO]) -> List[VerificationResult]:
    """
    Checks that all DOIs to be created from the given deposition file resolve to an actual document.

    The deposition file may only contain peer review elements.
    """
    parser = XmlParser()

    doi_batch = parser.parse(deposition_file, clazz=DoiBatch)

    reviews_by_preprint_doi: Dict[str, List[PeerReview]] = {}
    for r in doi_batch.body.peer_review:
        preprint_doi = r.program.related_item.inter_work_relation.value
        reviews_by_preprint_doi.setdefault(preprint_doi, [])
        reviews_by_preprint_doi[preprint_doi].append(r)

    return [
        verify_reviews_match(preprint_doi, reviews)
        for preprint_doi, reviews in reviews_by_preprint_doi.items()
    ]


def verify_reviews_match(preprint_doi: str, reviews: List[PeerReview]) -> VerificationResult:
    articles = get_articles(preprint_doi)
    if articles is None or len(articles) != 1:
        return VerificationResult(
            preprint_doi=preprint_doi,
            all_reviews_present=None,
            error=f'received no or multiple results from EEB for preprint DOI {preprint_doi}',
        )

    eeb_reviews = articles[0]['review_process']['reviews']
    num_reviews = len(reviews)
    num_eeb_reviews = len(eeb_reviews)
    all_reviews_present = num_eeb_reviews == num_reviews

    return VerificationResult(
        preprint_doi=preprint_doi,
        all_reviews_present=all_reviews_present,
        error=(
            None if all_reviews_present
            else f'deposition file wants to create DOIs for {num_reviews} reviews, but EEB only has {num_eeb_reviews}'
        ),
    )
