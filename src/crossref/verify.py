from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from xsdata.formats.dataclass.parsers import XmlParser
from src.crossref.xml.doi_batch import DoiBatch, PeerReview
from src.eeb.api import get_articles


@dataclass
class VerificationResult:
    preprint_doi: str
    all_reviews_present: Optional[bool] = None
    author_reply_matches: Optional[bool] = None
    error: Optional[str] = None


def verify(deposition_file: str) -> List[VerificationResult]:
    """
    Checks that all DOIs to be created from the given deposition file resolve to an actual document.

    The deposition file may only contain peer review elements.
    """
    parser = XmlParser()

    doi_batch = parser.parse(deposition_file, clazz=DoiBatch)

    reviews_by_preprint_doi: Dict[str, Tuple[List[PeerReview], Optional[PeerReview]]] = {}
    for review in doi_batch.body.peer_review:
        reviewed_article_relationships = [
            rel for rel in review.program.related_item
            if rel.inter_work_relation.relationship_type == 'isReviewOf'
        ]
        if len(reviewed_article_relationships) != 1:
            raise ValueError(f'Multiple isReviewOf relationships in deposition xml: {doi_batch}')
        preprint_doi = reviewed_article_relationships[0].inter_work_relation.value
        reviews_by_preprint_doi.setdefault(preprint_doi, ([], None))
        (reviews, author_reply) = reviews_by_preprint_doi[preprint_doi]

        if review.type == 'referee-report':
            reviews.append(review)
        elif review.type == 'author-comment':
            if author_reply:
                raise ValueError(f'Multiple author replies in deposition xml: {doi_batch}')
            author_reply = review

        reviews_by_preprint_doi[preprint_doi] = (reviews, author_reply)

    return [
        verify_reviews_match(preprint_doi, reviews, author_reply)
        for preprint_doi, (reviews, author_reply) in reviews_by_preprint_doi.items()
    ]


def verify_reviews_match(
    preprint_doi: str,
    reviews: List[PeerReview],
    author_reply: Optional[PeerReview],
) -> VerificationResult:
    articles = get_articles(preprint_doi)
    if articles is None or len(articles) != 1:
        return VerificationResult(
            preprint_doi=preprint_doi,
            error=f'received no or multiple results from EEB for preprint DOI {preprint_doi}',
        )

    review_process = articles[0]['review_process']
    eeb_reviews = review_process['reviews']
    num_reviews = len(reviews)
    num_eeb_reviews = len(eeb_reviews)
    all_reviews_present = num_eeb_reviews == num_reviews
    eeb_has_author_reply = review_process['response'] is not None
    deposition_has_author_reply = author_reply is not None
    author_reply_matches = eeb_has_author_reply == deposition_has_author_reply

    return VerificationResult(
        preprint_doi=preprint_doi,
        all_reviews_present=all_reviews_present,
        author_reply_matches=author_reply_matches,
        error=(
            None if all_reviews_present and author_reply_matches
            else (
                f'deposition file wants to create DOIs for {num_reviews} reviews'
                + f'{" and an author reply" if deposition_has_author_reply else ""}'
                + f' but EEB has {num_eeb_reviews} reviews'
                + f'{" and an author reply" if eeb_has_author_reply else " and no author reply"}'
            )
        ),
    )
